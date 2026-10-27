import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

import database

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    AUDIO_ENABLED = True
except Exception:
    AUDIO_ENABLED = False

IMAGE_FILENAME = "knight.png"

class DungeonPixelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DUNGEON QUEST // SEQUENTIAL RPG")
        self.root.geometry("680x800")
        self.root.config(bg="#110d0a")

        database.init_database()
        self.current_user_id = None
        self.current_username = None
        
        self.time_left = 30
        self.timer_active = False
        self.typing = False
        
        self.active_quest_id = None
        self.current_step = None
        self.current_correct_answer = ""
        self.current_reward = ""
        
        self.load_knight_image()
        self.play_audio("ambient.mp3", loops=-1)
        self.show_auth_screen()

    def play_audio(self, filename, loops=0):
        if AUDIO_ENABLED and os.path.exists(filename):
            try:
                sound = pygame.mixer.Sound(filename)
                sound.play(loops=loops)
            except Exception: pass

    def load_knight_image(self):
        try:
            if os.path.exists(IMAGE_FILENAME):
                img = Image.open(IMAGE_FILENAME)
                img = img.resize((65, 65), Image.Resampling.NEAREST)
                self.knight_photo = ImageTk.PhotoImage(img)
            else:
                self.knight_photo = None
        except Exception: self.knight_photo = None

    def clear_window(self):
        self.timer_active = False
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_auth_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=50)

        tk.Label(frame, text="† HERO LOGIN / REGISTER †", font=("Courier", 16, "bold"), fg="#d4af37", bg="#1a120b", pady=15).pack()

        tk.Label(frame, text="Username:", font=("Courier", 11, "bold"), fg="#e6c687", bg="#1a120b").pack(anchor="w", padx=30, pady=(10, 0))
        self.user_entry = tk.Entry(frame, font=("Courier", 12), bg="#110d0a", fg="#f0d2b6", insertbackground="white")
        self.user_entry.pack(fill=tk.X, padx=30, pady=5, ipady=4)

        tk.Label(frame, text="Password:", font=("Courier", 11, "bold"), fg="#e6c687", bg="#1a120b").pack(anchor="w", padx=30, pady=(10, 0))
        self.pass_entry = tk.Entry(frame, font=("Courier", 12), show="*", bg="#110d0a", fg="#f0d2b6", insertbackground="white")
        self.pass_entry.pack(fill=tk.X, padx=30, pady=5, ipady=4)

        btn_frame = tk.Frame(frame, bg="#1a120b")
        btn_frame.pack(fill=tk.X, padx=30, pady=25)

        tk.Button(btn_frame, text="[ LOGIN ]", font=("Courier", 10, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.handle_login).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(btn_frame, text="[ REGISTER ]", font=("Courier", 10, "bold"), bg="#2b2016", fg="#d4af37", command=self.handle_register).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=5)

    def handle_register(self):
        if database.register_user(self.user_entry.get().strip(), self.pass_entry.get().strip()):
            messagebox.showinfo("Success", "Registered! You may now login.")
        else:
            messagebox.showerror("Error", "Username already exists!")

    def handle_login(self):
        user_id = database.authenticate_user(self.user_entry.get().strip(), self.pass_entry.get().strip())
        if user_id:
            self.current_user_id = user_id
            self.current_username = self.user_entry.get().strip()
            self.play_audio("grind.wav")
            self.show_menu_screen()
        else:
            messagebox.showerror("Error", "Invalid credentials!")

    def show_menu_screen(self):
        self.clear_window()
        header = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        header.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(header, text=f"† HERO: {self.current_username.upper()} †", font=("Courier", 13, "bold"), fg="#d4af37", bg="#1a120b", pady=6).pack()
        
        badges = database.get_user_badges(self.current_user_id)
        tk.Label(header, text=f"BADGES: {', '.join(badges)}", font=("Courier", 10, "italic"), fg="#00ffcc", bg="#1a120b").pack(pady=(0, 6))
        
        nav_row = tk.Frame(header, bg="#1a120b")
        nav_row.pack(pady=5)
        tk.Button(nav_row, text="[ GLOBAL LEADERBOARD ]", font=("Courier", 8, "bold"), bg="#2b2016", fg="#ffcc00", command=self.show_leaderboard_screen).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_row, text="[ CREATE QUEST ]", font=("Courier", 8, "bold"), bg="#1e3d59", fg="#f5f0e1", command=self.show_quest_creator).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_row, text="[ LOGOUT ]", font=("Courier", 8, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.show_auth_screen).pack(side=tk.LEFT, padx=5)

        quests = database.get_all_quests()
        container = tk.Frame(self.root, bg="#110d0a")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        for q_id, q_title, creator in quests:
            card = tk.Frame(container, bg="#1c1510", bd=2, relief=tk.SOLID, highlightbackground="#594429", highlightthickness=1)
            card.pack(fill=tk.X, pady=6, ipady=4, ipadx=10)
            
            creator_text = f" (by {creator})" if creator else " (System)"
            tk.Label(card, text=f"⚔ {q_title}{creator_text}", font=("Courier", 10, "bold"), fg="#e6c687", bg="#1c1510").pack(anchor="w", padx=10, pady=(4, 2))
            tk.Button(card, text="[ ENTER DUNGEON ]", font=("Courier", 8, "bold"), bg="#4a1515", fg="#f0d2b6", command=lambda q=q_id: self.start_quest(q)).pack(anchor="e", padx=10, pady=(0, 4))

    def show_quest_creator(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(frame, text="† CUSTOM QUEST FORGE †", font=("Courier", 14, "bold"), fg="#ffcc00", bg="#1a120b", pady=10).pack()
        tk.Button(frame, text="◀ ABANDON FORGE", font=("Courier", 9, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.show_menu_screen).pack(anchor="w", padx=10)

        canvas = tk.Canvas(frame, bg="#110d0a", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#110d0a")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        tk.Label(scrollable_frame, text="Quest Title:", font=("Courier", 11, "bold"), fg="#e6c687", bg="#110d0a").pack(anchor="w", pady=(10, 2))
        title_entry = tk.Entry(scrollable_frame, font=("Courier", 12), bg="#261d15", fg="#f0d2b6", width=40)
        title_entry.pack(anchor="w", pady=(0, 15))

        riddle_entries = []
        for i in range(1, 4):
            step_frame = tk.Frame(scrollable_frame, bg="#1c1510", bd=1, relief=tk.SOLID)
            step_frame.pack(fill=tk.X, pady=10, padx=5, ipady=10)
            tk.Label(step_frame, text=f"Step {i}", font=("Courier", 12, "bold"), fg="#d4af37", bg="#1c1510").pack(anchor="w", padx=10)
            
            tk.Label(step_frame, text="Room Name:", fg="#a38f6d", bg="#1c1510").pack(anchor="w", padx=10)
            e_room = tk.Entry(step_frame, bg="#110d0a", fg="#fff", width=50); e_room.pack(anchor="w", padx=10)
            
            tk.Label(step_frame, text="Riddle Text:", fg="#a38f6d", bg="#1c1510").pack(anchor="w", padx=10)
            e_rid = tk.Entry(step_frame, bg="#110d0a", fg="#fff", width=50); e_rid.pack(anchor="w", padx=10)
            
            tk.Label(step_frame, text="Correct Answer:", fg="#a38f6d", bg="#1c1510").pack(anchor="w", padx=10)
            e_ans = tk.Entry(step_frame, bg="#110d0a", fg="#fff", width=50); e_ans.pack(anchor="w", padx=10)
            
            tk.Label(step_frame, text="Item Reward (e.g. 🗝️ Key):", fg="#a38f6d", bg="#1c1510").pack(anchor="w", padx=10)
            e_rew = tk.Entry(step_frame, bg="#110d0a", fg="#fff", width=50); e_rew.pack(anchor="w", padx=10)
            
            riddle_entries.append((e_room, e_rid, e_ans, e_rew))

        def submit_quest():
            q_title = title_entry.get().strip()
            if not q_title:
                messagebox.showerror("Error", "Quest needs a title!"); return
                
            final_riddles = []
            for entries in riddle_entries:
                r_name = entries[0].get().strip()
                r_text = entries[1].get().strip()
                r_ans = entries[2].get().strip()
                r_rew = entries[3].get().strip()
                if not (r_name and r_text and r_ans and r_rew):
                    messagebox.showerror("Error", "All steps must be filled out!"); return
                final_riddles.append((r_name, r_text, r_ans, r_rew))
                
            database.save_custom_quest(self.current_user_id, q_title, final_riddles)
            messagebox.showinfo("Success", "Custom Quest Forged!")
            self.show_menu_screen()

        tk.Button(scrollable_frame, text="[ FORGE QUEST & PUBLISH ]", font=("Courier", 12, "bold"), bg="#1e3d59", fg="#f5f0e1", command=submit_quest).pack(pady=20)

    def show_leaderboard_screen(self):
        self.clear_window()
        frame = tk.Frame(self.root, bg="#1a120b", bd=3, relief=tk.RAISED)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        tk.Label(frame, text="† HALL OF HEROES †", font=("Courier", 14, "bold"), fg="#ffcc00", bg="#1a120b", pady=10).pack()
        
        txt = tk.Text(frame, font=("Courier", 10), bg="#110d0a", fg="#00ffcc", padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        txt.insert(tk.END, f"{'RANK':<5}{'HERO':<12}{'SCORE':<8}{'BADGES'}\n")
        txt.insert(tk.END, "-"*65 + "\n")
        
        for idx, (un, ts, badges) in enumerate(database.get_top_scores(), 1):
            txt.insert(tk.END, f"{idx:<5}{un:<12}{str(ts):<8}{badges}\n")
            
        txt.config(state=tk.DISABLED)
        tk.Button(frame, text="[ BACK ]", font=("Courier", 10, "bold"), bg="#4a1515", fg="#f0d2b6", command=self.show_menu_screen).pack(pady=10)

    def start_quest(self, quest_id):
        self.play_audio("grind.wav")
        database.setup_active_session(self.current_user_id, quest_id)
        self.show_game_screen()

    def show_game_screen(self):
        self.clear_window()
        
        top_bar = tk.Frame(self.root, bg="#1a120b", bd=2, relief=tk.RAISED)
        top_bar.pack(fill=tk.X, padx=15, pady=10)
        tk.Button(top_bar, text="◀ FLEE DUNGEON", font=("Courier", 9, "bold"), bg="#2b2016", fg="#d4af37", command=self.show_menu_screen).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.timer_label = tk.Label(top_bar, text="TIME: 30s", font=("Courier", 12, "bold"), fg="#ff3333", bg="#1a120b")
        self.timer_label.pack(side=tk.RIGHT, padx=15)

        meta = tk.Frame(self.root, bg="#110d0a")
        meta.pack(fill=tk.X, padx=15, pady=5)
        self.quest_label = tk.Label(meta, text="QUEST:", font=("Courier", 11, "bold"), fg="#d4af37", bg="#110d0a")
        self.quest_label.pack(anchor="w")
        self.room_label = tk.Label(meta, text="ROOM:", font=("Courier", 10), fg="#a38f6d", bg="#110d0a")
        self.room_label.pack(anchor="w")

        riddle_container = tk.Frame(self.root, bg="#1d1611", bd=3, relief=tk.SUNKEN)
        riddle_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        self.riddle_text = tk.Text(riddle_container, wrap=tk.WORD, font=("Courier", 12), bg="#1d1611", fg="#e8d5b7", padx=15, pady=15, relief=tk.FLAT, height=5)
        self.riddle_text.pack(fill=tk.BOTH, expand=True)
        self.riddle_text.config(state=tk.DISABLED)

        interaction = tk.Frame(self.root, bg="#150f0a", bd=2, relief=tk.SOLID, highlightbackground="#3d2c1d")
        interaction.pack(fill=tk.X, padx=15, pady=5)
        
        bubble_frame = tk.Frame(interaction, bg="#150f0a")
        bubble_frame.pack(fill=tk.X, padx=10, pady=8)

        sprite_frame = tk.Frame(bubble_frame, bg="#211811", width=75, height=75, bd=2, relief=tk.RAISED)
        sprite_frame.pack(side=tk.LEFT, padx=(0, 15))
        sprite_frame.pack_propagate(False)
        if self.knight_photo:
            tk.Label(sprite_frame, image=self.knight_photo, bg="#211811").pack(expand=True)
        else:
            tk.Label(sprite_frame, text="🛡️", font=("Arial", 22), bg="#211811").pack(expand=True)

        bubble_container = tk.Frame(bubble_frame, bg="#261d15", bd=2, relief=tk.SOLID)
        bubble_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(bubble_container, text="ACTION (Type Answer to the Riddle):", font=("Courier", 8, "bold"), fg="#a38f6d", bg="#261d15").pack(anchor="w", padx=8, pady=(4, 0))
        
        self.speech_entry = tk.Entry(bubble_container, font=("Courier", 11, "bold"), bg="#110d0a", fg="#f0d2b6", insertbackground="white")
        self.speech_entry.pack(fill=tk.X, padx=8, pady=6, ipady=4)
        self.speech_entry.bind("<Return>", lambda event: self.process_input())

        btn_sub = tk.Frame(interaction, bg="#150f0a")
        btn_sub.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Button(btn_sub, text="[ HINT (-50) ]", font=("Courier", 10, "bold"), bg="#2b2016", fg="#00ffcc", command=self.use_hint).pack(side=tk.LEFT)
        tk.Button(btn_sub, text="ACT ⚔", font=("Courier", 10, "bold"), bg="#5e1914", fg="#f0d2b6", command=self.process_input).pack(side=tk.RIGHT)

        footer = tk.Frame(self.root, bg="#1c1510", bd=2, relief=tk.SOLID, highlightbackground="#594429")
        footer.pack(fill=tk.X, padx=15, pady=10, ipady=4)
        self.score_label = tk.Label(footer, text="SCORE: 100", font=("Courier", 9, "bold"), fg="#6ba868", bg="#1c1510")
        self.score_label.pack(side=tk.LEFT, padx=10)
        self.inventory_label = tk.Label(footer, text="RELICS: [ NONE ]", font=("Courier", 9, "bold"), fg="#8c7853", bg="#1c1510")
        self.inventory_label.pack(anchor="w", pady=(20, 0), padx=10)

        self.load_room_state()

    def type_riddle(self, text, index=0):
        if not self.timer_active: return
        self.typing = True
        if index == 0:
            self.riddle_text.config(state=tk.NORMAL)
            self.riddle_text.delete("1.0", tk.END)
        if index < len(text):
            self.riddle_text.insert(tk.END, text[index])
            self.riddle_text.see(tk.END)
            self.root.after(25, self.type_riddle, text, index + 1)
        else:
            self.riddle_text.config(state=tk.DISABLED)
            self.typing = False

    def trigger_screen_shake(self, count=0):
        self.play_audio("error.wav")
        if count < 6:
            offset = 10 if count % 2 == 0 else -10
            color = "#4a0000" if count % 2 == 0 else "#110d0a"
            self.root.config(bg=color)
            self.root.geometry(f"+{self.root.winfo_x() + offset}+{self.root.winfo_y()}")
            self.root.after(50, self.trigger_screen_shake, count + 1)
        else:
            self.root.config(bg="#110d0a")

    def countdown_timer(self):
        if not self.timer_active: return
        if self.time_left > 0:
            self.timer_label.config(text=f"TIME: {self.time_left}s")
            self.time_left -= 1
            self.root.after(1000, self.countdown_timer)
        else:
            self.speech_entry.delete(0, tk.END)
            self.process_input(time_out=True)

    def refresh_stats(self):
        player = database.get_player_state(self.current_user_id)
        if player:
            _, _, score, inventory = player
            self.score_label.config(text=f"SCORE: {score}")
            self.inventory_label.config(text=f"RELICS: [ {inventory} ]")

    def load_room_state(self):
        player = database.get_player_state(self.current_user_id)
        if not player: return
        self.active_quest_id, self.current_step, score, inventory = player
        
        room_data = database.get_room_data(self.active_quest_id, self.current_step)
        if not room_data: return
        
        q_title, r_name, r_text, self.current_correct_answer, self.current_reward = room_data

        self.quest_label.config(text=f"QUEST: {q_title}")
        self.room_label.config(text=f"LOCATION [Step {self.current_step}]: {r_name}")
        self.refresh_stats()
        self.speech_entry.delete(0, tk.END)
        
        self.time_left = 30
        self.timer_active = True
        
        self.type_riddle(f'"{r_text}"')
        self.countdown_timer()

    def use_hint(self):
        if not self.current_correct_answer: return
        database.penalize_score(self.current_user_id, 50)
        hint = f"Starts with '{self.current_correct_answer[0].upper()}', Length: {len(self.current_correct_answer)}"
        messagebox.showinfo("Mystic Sage", hint)
        self.refresh_stats()

    def process_input(self, time_out=False):
        self.timer_active = False 
        user_input = self.speech_entry.get().strip().upper()
        
        player = database.get_player_state(self.current_user_id)
        _, _, score, inventory = player
        
        if user_input.lower() == self.current_correct_answer.lower() and not time_out:
            self.play_audio("clash.wav")
            speed_bonus = 150 if self.time_left >= 15 else 0
            
            total_steps = database.get_quest_length(self.active_quest_id)
            is_final_step = (self.current_step == total_steps)
            
            if is_final_step:
                new_score = score + 150 + speed_bonus
                database.complete_quest(self.current_user_id, self.active_quest_id, new_score)
                msg = f"QUEST CONQUERED!\n\nFINAL SCORE: {new_score}\n\nCheck the Hero Menu for any new Badges!"
                self.show_victory_screen(msg)
            else:
                database.solve_riddle(self.current_user_id, self.current_step, score, inventory, self.current_reward, speed_bonus)
                messagebox.showinfo("Seal Broken!", f"Correct! Acquired {self.current_reward}. Speed Bonus: +{speed_bonus}")
                self.load_room_state()
        else:
            self.trigger_screen_shake()
            database.penalize_score(self.current_user_id, 20)
            
            msg = "Time ran out!" if time_out else "The dungeon rejects your answer (-20 Score)."
            messagebox.showerror("Curse", msg)
            self.refresh_stats()
            
            self.time_left = 30
            self.timer_active = True
            self.countdown_timer() 

    def show_victory_screen(self, outcome_msg):
        self.timer_active = False
        self.play_audio("grind.wav")
        self.riddle_text.config(state=tk.NORMAL)
        self.riddle_text.delete("1.0", tk.END)
        self.riddle_text.insert(tk.END, f"† GLORY †\n\n{outcome_msg}")
        self.riddle_text.config(state=tk.DISABLED)
        self.speech_entry.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = DungeonPixelApp(root)
    root.mainloop()