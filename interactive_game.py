import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Attempt to load Pygame for audio, gracefully fallback if not installed
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

import database

IMAGE_FILENAME = "knight.png"

class DungeonPixelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DUNGEON QUEST")
        self.root.geometry("680x780")
        self.root.config(bg="#110d0a")
        
        self.typewriter_active = False
        self.timer_job = None
        self.time_left = 30
        self.current_correct_answer = ""
        
        database.init_database()
        self.current_user_id = None
        self.current_username = None
        
        self.load_knight_image()
        self.play_bgm("ambient.mp3") # Plays if file exists
        self.show_auth_screen()

    # ==========================================
    # AUDIO & VISUAL EFFECTS LOGIC
    # ==========================================
    def play_sfx(self, filename):
        if AUDIO_ENABLED and os.path.exists(filename):
            pygame.mixer.Sound(filename).play()

    def play_bgm(self, filename):
        if AUDIO_ENABLED and os.path.exists(filename):
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play(-1) # Loop endlessly

    def trigger_damage_effect(self, flash_count=0):
        """Creates a screen shake and rapid red flashing effect."""
        self.play_sfx("error.wav")
        if flash_count < 6:
            color = "#5e1914" if flash_count % 2 == 0 else "#110d0a"
            self.root.config(bg=color)
            
            try:
                x, y = self.root.winfo_x(), self.root.winfo_y()
                offset = 15 if flash_count % 2 == 0 else -15
                self.root.geometry(f"+{x+offset}+{y}")
            except tk.TclError:
                pass # Failsafe if window is moving

            self.root.after(60, self.trigger_damage_effect, flash_count + 1)
        else:
            self.root.config(bg="#110d0a") # Restore normal background

    def type_text(self, text, index=0):
        """RPG Typewriter Effect for the Riddle text."""
        if index == 0:
            self.typewriter_active = True
            self.riddle_text.config(state=tk.NORMAL)
            self.riddle_text.delete("1.0", tk.END)
            self.submit_btn.config(state=tk.DISABLED)
            
        if index < len(text):
            self.riddle_text.insert(tk.END, text[index])
            self.riddle_text.see(tk.END)
            # Faster typing speed
            self.root.after(25, self.type_text, text, index + 1)
        else:
            self.riddle_text.config(state=tk.DISABLED)
            self.typewriter_active = False
            self.submit_btn.config(state=tk.NORMAL)
            self.start_timer() # Start timer ONLY after reading is done

    def start_timer(self):
        self.time_left = 30
        self.update_timer()

    def update_timer(self):
        if self.time_left > 0:
            color = "#6ba868" if self.time_left > 10 else "#ff4444"
            self.timer_label.config(text=f"⏳ TIME: {self.time_left}s", fg=color)
            self.time_left -= 1
            self.timer_job = self.root.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="⏳ TIME OUT!", fg="#ff4444")
            self.speech_entry.delete(0, tk.END)
            self.submit_answer(timeout=True)

    def stop_timer(self):
        if self.timer_job is not None:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

    # ==========================================
    # CORE UI & IMAGE LOGIC
    # ==========================================
    def load_knight_image(self):
        try:
            if os.path.exists(IMAGE_FILENAME):
                img = Image.open(IMAGE_FILENAME)
                img = img.resize((65, 65), Image.Resampling.NEAREST)
                self.knight_photo = ImageTk.PhotoImage(img)
            else:
                self.knight_photo = None
        except Exception:
            self.knight_photo = None

    def clear_window(self):
        self.stop_timer()
        for widget in self.root.winfo_children():
            widget.destroy()

    # ==========================================
    # AUTHENTICATION SCREEN
    # ==========================================
    def show_auth_screen(self):
        self.clear_window()

        frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=50)

        tk.Label(frame, text="† HERO LOGIN / REGISTER †", font=("Courier", 16, "bold"), fg="#d4af37", bg="#1a120b", pady=15).pack()

        tk.Label(frame, text="Username:", font=("Courier", 11, "bold"), fg="#e6c687", bg="#1a120b").pack(anchor="w", padx=30, pady=(10, 0))
        self.user_entry = tk.Entry(frame, font=("Courier", 12), bg="#110d0a", fg="#f0d2b6", insertbackground="white", relief=tk.SOLID, bd=1)
        self.user_entry.pack(fill=tk.X, padx=30, pady=5, ipady=4)

        tk.Label(frame, text="Password:", font=("Courier", 11, "bold"), fg="#e6c687", bg="#1a120b").pack(anchor="w", padx=30, pady=(10, 0))
        self.pass_entry = tk.Entry(frame, font=("Courier", 12), show="*", bg="#110d0a", fg="#f0d2b6", insertbackground="white", relief=tk.SOLID, bd=1)
        self.pass_entry.pack(fill=tk.X, padx=30, pady=5, ipady=4)

        btn_frame = tk.Frame(frame, bg="#1a120b")
        btn_frame.pack(fill=tk.X, padx=30, pady=25)

        tk.Button(btn_frame, text="[ LOGIN ]", font=("Courier", 10, "bold"), bg="#4a1515", fg="#f0d2b6", relief=tk.RAISED, bd=2, command=self.handle_login).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(btn_frame, text="[ REGISTER ]", font=("Courier", 10, "bold"), bg="#2b2016", fg="#d4af37", relief=tk.RAISED, bd=2, command=self.handle_register).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def handle_register(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Warning", "Enter both username and password.")
            return

        success = database.register_user(username, password)
        if success:
            messagebox.showinfo("Success", "Account registered successfully! You may now login.")
        else:
            self.trigger_damage_effect()
            messagebox.showerror("Error", "Username already exists!")

    def handle_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Warning", "Enter both username and password.")
            return

        user_id = database.authenticate_user(username, password)
        if user_id:
            self.play_sfx("grind.wav")
            self.current_user_id = user_id
            self.current_username = username
            self.show_menu_screen()
        else:
            self.trigger_damage_effect()
            messagebox.showerror("Error", "Invalid username or password!")

    # ==========================================
    # MENU SCREEN & LEADERBOARD VIEWER
    # ==========================================
    def show_menu_screen(self):
        self.clear_window()

        header_frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        header_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(header_frame, text=f"† HERO: {self.current_username.upper()} †", font=("Courier", 13, "bold"), fg="#d4af37", bg="#1a120b", pady=6).pack()
        
        nav_row = tk.Frame(header_frame, bg="#1a120b")
        nav_row.pack(pady=5)
        tk.Button(nav_row, text="[ + CREATE QUEST ]", font=("Courier", 8, "bold"), bg="#2b2016", fg="#00ffcc", command=self.show_creator_screen).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_row, text="[ HIGH SCORES ]", font=("Courier", 8, "bold"), bg="#2b2016", fg="#ffcc00", command=self.show_leaderboard_screen).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_row, text="[ LOGOUT ]", font=("Courier", 8, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.show_auth_screen).pack(side=tk.LEFT, padx=5)

        quests = database.get_all_quests()

        quests_container = tk.Frame(self.root, bg="#110d0a")
        quests_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        for q_id, q_title, q_location, creator in quests:
            card = tk.Frame(quests_container, bg="#1c1510", bd=2, relief=tk.SOLID, highlightbackground="#594429", highlightthickness=1)
            card.pack(fill=tk.X, pady=6, ipady=4, ipadx=10)

            tk.Label(card, text=f"⚔ {q_title} (By: {creator})", font=("Courier", 10, "bold"), fg="#e6c687", bg="#1c1510").pack(anchor="w", padx=10, pady=(4, 2))
            tk.Label(card, text=f"CHAMBER ZONE: {q_location}", font=("Courier", 9), fg="#a38f6d", bg="#1c1510").pack(anchor="w", padx=10, pady=(0, 4))

            select_btn = tk.Button(
                card, text="[ ENTER ]", font=("Courier", 8, "bold"),
                bg="#4a1515", fg="#f0d2b6", activebackground="#7a2424", activeforeground="white",
                relief=tk.RAISED, bd=2, command=lambda quest_id=q_id: self.start_quest(quest_id)
            )
            select_btn.pack(anchor="e", padx=10, pady=(0, 4))

    # ==========================================
    # CUSTOM QUEST CREATOR SCREEN
    # ==========================================
    def show_creator_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(frame, text="† CUSTOM DUNGEON †", font=("Courier", 14, "bold"), fg="#00ffcc", bg="#1a120b", pady=10).pack()

        form_frame = tk.Frame(frame, bg="#1a120b")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        tk.Label(form_frame, text="Quest Title:", font=("Courier", 9, "bold"), fg="#e6c687", bg="#1a120b").pack(anchor="w")
        self.c_title = tk.Entry(form_frame, font=("Courier", 10), bg="#110d0a", fg="#f0d2b6", insertbackground="white")
        self.c_title.pack(fill=tk.X, pady=(0, 5), ipady=2)

        tk.Label(form_frame, text="Dungeon Zone Name:", font=("Courier", 9, "bold"), fg="#e6c687", bg="#1a120b").pack(anchor="w")
        self.c_zone = tk.Entry(form_frame, font=("Courier", 10), bg="#110d0a", fg="#f0d2b6", insertbackground="white")
        self.c_zone.pack(fill=tk.X, pady=(0, 10), ipady=2)

        self.clue_entries = []
        clues_scroll_frame = tk.Frame(form_frame, bg="#140b06", bd=2, relief=tk.SUNKEN)
        clues_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        tk.Label(clues_scroll_frame, text="Enter Exactly 5 Riddles & Answers:", font=("Courier", 9, "bold"), fg="#ffcc00", bg="#140b06").pack(anchor="w", padx=5, pady=2)

        for i in range(1, 6):
            row = tk.Frame(clues_scroll_frame, bg="#140b06")
            row.pack(fill=tk.X, padx=5, pady=2)
            
            tk.Label(row, text=f"#{i} Riddle:", font=("Courier", 8), fg="#ccc", bg="#140b06", width=10).pack(side=tk.LEFT)
            r_ent = tk.Entry(row, font=("Courier", 9), bg="#110d0a", fg="#fff")
            r_ent.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

            tk.Label(row, text="Ans:", font=("Courier", 8), fg="#ccc", bg="#140b06", width=4).pack(side=tk.LEFT)
            a_ent = tk.Entry(row, font=("Courier", 9), bg="#110d0a", fg="#fff", width=10)
            a_ent.pack(side=tk.LEFT, padx=2)

            self.clue_entries.append((r_ent, a_ent))

        btn_row = tk.Frame(frame, bg="#1a120b")
        btn_row.pack(fill=tk.X, padx=20, pady=10)
        tk.Button(btn_row, text="[ SAVE QUEST ]", font=("Courier", 10, "bold"), bg="#00ffcc", fg="black", command=self.save_custom_quest).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(btn_row, text="[ CANCEL ]", font=("Courier", 10, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.show_menu_screen).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def save_custom_quest(self):
        q_title = self.c_title.get().strip()
        q_zone = self.c_zone.get().strip()

        if not q_title or not q_zone:
            messagebox.showwarning("Error", "Please provide a Quest Title and Zone name.")
            return

        clue_data_list = []
        for r_ent, a_ent in self.clue_entries:
            r = r_ent.get().strip()
            a = a_ent.get().strip()
            if not r or not a:
                messagebox.showwarning("Error", "All 5 riddles and answers must be filled out!")
                return
            clue_data_list.append((r, a))

        database.create_custom_quest(q_title, q_zone, self.current_username, clue_data_list)
        messagebox.showinfo("Success", "Your custom dungeon quest has been forged and saved to the realm!")
        self.show_menu_screen()

    # ==========================================
    # LEADERBOARD / HIGH SCORES SCREEN
    # ==========================================
    def show_leaderboard_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(frame, text="† HALL OF HEROES (HIGH SCORES) †", font=("Courier", 14, "bold"), fg="#ffcc00", bg="#1a120b", pady=10).pack()

        score_text = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10), bg="#110d0a", fg="#00ffcc", padx=10, pady=10)
        score_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        top_scores = database.get_top_scores()

        if not top_scores:
            score_text.insert(tk.END, "No quests completed yet. Be the first hero to conquer a dungeon!")
        else:
            score_text.insert(tk.END, f"{'RANK':<6}{'HERO':<15}{'QUEST':<25}{'SCORE':<8}{'DATE'}\n")
            score_text.insert(tk.END, "-"*65 + "\n")
            for idx, (uname, qname, fscore, dplayed) in enumerate(top_scores, start=1):
                score_text.insert(tk.END, f"{idx:<6}{uname:<15}{qname[:22]:<25}{fscore:<8}{dplayed}\n")

        score_text.config(state=tk.DISABLED)
        tk.Button(frame, text="[ BACK TO MENU ]", font=("Courier", 10, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.show_menu_screen).pack(pady=10)

    # ==========================================
    # GAMEPLAY LOGIC
    # ==========================================
    def start_quest(self, quest_id):
        self.play_sfx("grind.wav")
        database.setup_active_session(self.current_user_id, quest_id)
        self.show_game_screen()

    def show_game_screen(self):
        self.clear_window()

        top_bar = tk.Frame(self.root, bg="#1a120b", bd=2, relief=tk.RAISED)
        top_bar.pack(fill=tk.X, padx=15, pady=10)

        back_btn = tk.Button(
            top_bar, text="◀ CAMP", font=("Courier", 9, "bold"), 
            bg="#2b2016", fg="#d4af37", relief=tk.RAISED, bd=2, command=self.show_menu_screen
        )
        back_btn.pack(side=tk.LEFT, padx=5, pady=5)

        tk.Label(top_bar, text=f"PLAYER: {self.current_username.upper()}", font=("Courier", 10, "bold"), fg="#c2a26d", bg="#1a120b").pack(side=tk.LEFT, expand=True)
        
        self.timer_label = tk.Label(top_bar, text="⏳ TIME: 30s", font=("Courier", 10, "bold"), fg="#6ba868", bg="#1a120b")
        self.timer_label.pack(side=tk.RIGHT, padx=10)

        meta_frame = tk.Frame(self.root, bg="#110d0a")
        meta_frame.pack(fill=tk.X, padx=15, pady=5)

        self.case_label = tk.Label(meta_frame, text="QUEST: Loading...", font=("Courier", 11, "bold"), fg="#d4af37", bg="#110d0a")
        self.case_label.pack(anchor="w")

        self.location_label = tk.Label(meta_frame, text="CHAMBER: Loading...", font=("Courier", 10), fg="#8c7853", bg="#110d0a")
        self.location_label.pack(anchor="w", pady=(2, 0))

        riddle_container = tk.Frame(self.root, bg="#1d1611", bd=3, relief=tk.SUNKEN)
        riddle_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)

        self.riddle_text = tk.Text(
            riddle_container, wrap=tk.WORD, font=("Courier", 12), 
            bg="#1d1611", fg="#e8d5b7", padx=15, pady=15, relief=tk.FLAT, height=5
        )
        self.riddle_text.pack(fill=tk.BOTH, expand=True)

        interaction_area = tk.Frame(self.root, bg="#150f0a", bd=2, relief=tk.SOLID, highlightbackground="#3d2c1d")
        interaction_area.pack(fill=tk.X, padx=15, pady=5)

        char_bubble_frame = tk.Frame(interaction_area, bg="#150f0a")
        char_bubble_frame.pack(fill=tk.X, padx=10, pady=8)

        sprite_frame = tk.Frame(char_bubble_frame, bg="#211811", width=75, height=75, bd=2, relief=tk.RAISED)
        sprite_frame.pack(side=tk.LEFT, padx=(0, 15))
        sprite_frame.pack_propagate(False)

        if self.knight_photo:
            sprite_label = tk.Label(sprite_frame, image=self.knight_photo, bg="#211811")
            sprite_label.pack(expand=True)
        else:
            sprite_label = tk.Label(sprite_frame, text="🛡️", font=("Arial", 22), bg="#211811")
            sprite_label.pack(expand=True)

        bubble_container = tk.Frame(char_bubble_frame, bg="#261d15", bd=2, relief=tk.SOLID, highlightbackground="#8c7853")
        bubble_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(bubble_container, text="HERO'S SPOKEN INCANTATION (Type Answer):", font=("Courier", 8, "bold"), fg="#a38f6d", bg="#261d15").pack(anchor="w", padx=8, pady=(4, 0))

        self.speech_entry = tk.Entry(bubble_container, font=("Courier", 11, "bold"), bg="#110d0a", fg="#f0d2b6", insertbackground="white", relief=tk.SOLID, bd=1)
        self.speech_entry.pack(fill=tk.X, padx=8, pady=6, ipady=4)
        self.speech_entry.bind("<Return>", lambda event: self.submit_answer())

        btn_sub_frame = tk.Frame(interaction_area, bg="#150f0a")
        btn_sub_frame.pack(fill=tk.X, padx=10, pady=(0, 8))

        self.hint_btn = tk.Button(
            btn_sub_frame, text="[ USE HINT -50 ]", font=("Courier", 9, "bold"), 
            bg="#2b2016", fg="#00ffcc", relief=tk.RAISED, bd=2, command=self.use_hint
        )
        self.hint_btn.pack(side=tk.LEFT)

        self.submit_btn = tk.Button(
            btn_sub_frame, text="CHALLENGE WITH ANSWER ⚔", font=("Courier", 10, "bold"), 
            bg="#5e1914", fg="#f0d2b6", activebackground="#8c251e", activeforeground="white",
            relief=tk.RAISED, bd=2, command=self.submit_answer
        )
        self.submit_btn.pack(side=tk.RIGHT)

        footer_frame = tk.Frame(self.root, bg="#1c1510", bd=2, relief=tk.SOLID, highlightbackground="#594429")
        footer_frame.pack(fill=tk.X, padx=15, pady=10, ipady=4)

        stats_sub = tk.Frame(footer_frame, bg="#1c1510")
        stats_sub.pack(fill=tk.X, padx=10, pady=4)

        self.clues_label = tk.Label(stats_sub, text="CLUES SOLVED: 0/5", font=("Courier", 9, "bold"), fg="#d4af37", bg="#1c1510")
        self.clues_label.pack(side=tk.LEFT)

        self.score_label = tk.Label(stats_sub, text="SOULS/SCORE: 100", font=("Courier", 9, "bold"), fg="#6ba868", bg="#1c1510")
        self.score_label.pack(side=tk.RIGHT)

        inventory_sub = tk.Frame(footer_frame, bg="#1c1510")
        inventory_sub.pack(fill=tk.X, padx=10, pady=(2, 0))

        # Re-styled inventory label mapping
        self.inventory_label = tk.Label(inventory_sub, text="RELICS HELD: [ NONE ]", font=("Courier", 10, "bold"), fg="#ffcc00", bg="#1c1510")
        self.inventory_label.pack(anchor="w")

        self.load_game_state()

    def use_hint(self):
        """Deducts points to reveal first letter and length of answer."""
        if self.typewriter_active: return
        
        player = database.get_player_progress(self.current_user_id)
        if not player or not self.current_correct_answer: return
        
        current_score = player[1]
        new_score = max(0, current_score - 50)
        database.update_player_score(self.current_user_id, new_score)
        self.score_label.config(text=f"SOULS/SCORE: {new_score}")
        
        hint_text = f"The Sage whispers: The word is {len(self.current_correct_answer)} letters long, starting with '{self.current_correct_answer[0].upper()}'."
        messagebox.showinfo("Hint Acquired", hint_text)

    def load_game_state(self):
        self.stop_timer()
        
        player = database.get_player_progress(self.current_user_id)
        if not player: return
        active_quest_id, score, clues_found, inventory, _ = player
        quest_title = database.get_quest_title(active_quest_id)

        if clues_found >= 5:
            self.show_victory_screen(quest_title, active_quest_id, score, inventory)
            return

        clue = database.get_current_clue(self.current_user_id)
        if not clue:
            self.show_victory_screen(quest_title, active_quest_id, score, inventory)
            return

        clue_id, location_name, riddle_text, correct_answer, item_reward = clue
        self.current_correct_answer = correct_answer

        self.case_label.config(text=f"QUEST: {quest_title}")
        self.location_label.config(text=f"CHAMBER: {location_name}")
        
        self.clues_label.config(text=f"CLUES SOLVED: {clues_found}/5")
        self.score_label.config(text=f"SOULS/SCORE: {score}")
        self.inventory_label.config(text=f"RELICS HELD:\n[ {inventory} ]")

        self.speech_entry.delete(0, tk.END)
        
        # Trigger RPG Typewriter Text Reveal
        self.type_text(f'"{riddle_text}"')

    def submit_answer(self, timeout=False):
        if self.typewriter_active: return
        self.stop_timer()
        
        user_answer = self.speech_entry.get().strip().lower()
        if not user_answer and not timeout:
            messagebox.showwarning("Warning", "Your hero remains silent! Type an answer.")
            self.start_timer() # Resume timer if accidental click
            return

        player = database.get_player_progress(self.current_user_id)
        active_quest_id, score, clues_found, inventory, _ = player
        
        # --- CHEAT CODES IMPLEMENTATION ---
        if user_answer == "iddqd":
            self.play_sfx("clash.wav")
            database.update_player_score(self.current_user_id, score + 500)
            messagebox.showinfo("God Mode", "Cheat activated! +500 Souls.")
            self.load_game_state()
            return
        elif user_answer == "heal":
            self.play_sfx("clash.wav")
            inv = "❤️ Phoenix Down" if inventory == "None" else inventory + "  ❤️ Phoenix Down"
            database.update_player_progress(self.current_user_id, score, clues_found, inv)
            messagebox.showinfo("Healing", "Cheat activated! Received Phoenix Down.")
            self.load_game_state()
            return

        # Normal verification
        clue = database.get_current_clue(self.current_user_id)
        if not clue: return
        
        clue_id, location_name, riddle_text, correct_answer, item_reward = clue

        if user_answer == correct_answer.lower():
            self.play_sfx("clash.wav")
            new_clues_found = clues_found + 1
            
            # Speed Bonus calculation
            earned_points = 150
            if self.time_left >= 15:
                earned_points = 300 # 2x Bonus
                messagebox.showinfo("Speed Bonus!", f"Incredible speed! Seal broken quickly (+{earned_points} points).")
            else:
                messagebox.showinfo("Seal Broken!", "Your incantation echoes correctly through the stone halls! Relic acquired.")
                
            new_score = score + earned_points

            new_inventory = item_reward if inventory == "None" else f"{inventory}  {item_reward}"

            database.update_player_progress(self.current_user_id, new_score, new_clues_found, new_inventory)
            self.load_game_state()
        else:
            self.trigger_damage_effect() # Screen Shake and Flash
            new_score = max(0, score - 20)
            database.update_player_score(self.current_user_id, new_score)
            
            msg = "TIME OUT! The trap triggered (-20 Score)." if timeout else "The dungeon rejects your answer (-20 Score). Listen closely to the riddle!"
            messagebox.showerror("Curse Triggered", msg)
            
            self.score_label.config(text=f"SOULS/SCORE: {new_score}")
            self.start_timer() # Restart timer for another try

    def show_victory_screen(self, quest_title, quest_id, score, inventory):
        self.stop_timer()
        self.play_sfx("grind.wav")
        database.save_score_history(self.current_user_id, quest_id, score)

        self.location_label.config(text="CHAMBER: CONQUERED")
        self.riddle_text.config(state=tk.NORMAL)
        self.riddle_text.delete("1.0", tk.END)
        self.riddle_text.insert(
            tk.END, 
            f"† CONQUERED: {quest_title} †\n\nYou have survived the depths and unlocked all 5 randomized dungeon secrets!\n\nFINAL SCORE: {score} (Saved to Hall of Heroes)\n\nRELICS COLLECTED:\n[ {inventory} ]"
        )
        self.riddle_text.config(state=tk.DISABLED)
        self.speech_entry.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED)
        self.hint_btn.config(state=tk.DISABLED)
        self.clues_label.config(text="CLUES SOLVED: 5/5")
        self.timer_label.config(text="⏳ QUEST COMPLETE")


if __name__ == "__main__":
    root = tk.Tk()
    app = DungeonPixelApp(root)
    root.mainloop()