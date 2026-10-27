import sqlite3
import hashlib

DB_NAME = "MystiQuest.db"

def hash_password(password):
    """Cryptographic hashing for security requirements."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_connection():
    """Returns a new SQLite database connection."""
    return sqlite3.connect(DB_NAME)

def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # TABLE 1: Users (Tracks authentication and live session state)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            active_quest_id INTEGER DEFAULT NULL,
            current_step INTEGER DEFAULT NULL,
            score INTEGER DEFAULT 0,
            inventory TEXT DEFAULT 'None'
        )
    """)
    
    # TABLE 2: Quests (Combines Quest metadata and Sequential Riddles into one table)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_id INTEGER,
            title TEXT,
            creator_id INTEGER,
            step_number INTEGER,
            room_name TEXT,
            riddle_text TEXT,
            correct_answer TEXT,
            item_reward TEXT
        )
    """)

    # TABLE 3: Score History (Logs completed runs and holds dynamically triggered Badges)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quest_id INTEGER,
            final_score INTEGER,
            badge_earned TEXT DEFAULT 'None',
            date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # SQL TRIGGER 1: Award badge for a flawless run, explicitly marking which Quest ID it came from
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_badge_flawless
        AFTER INSERT ON score_history
        WHEN NEW.final_score >= 250
        BEGIN
            UPDATE score_history 
            SET badge_earned = CASE 
                WHEN badge_earned = 'None' THEN '🎖️ Flawless (Q' || NEW.quest_id || ')' 
                ELSE badge_earned || ', 🎖️ Flawless (Q' || NEW.quest_id || ')' 
            END
            WHERE id = NEW.id;
        END;
    """)

    # SQL TRIGGER 2: Award badge after completing 3 quests, marking the Quest ID that triggered the milestone
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_badge_veteran
        AFTER INSERT ON score_history
        WHEN (SELECT COUNT(id) FROM score_history WHERE user_id = NEW.user_id) = 3
        BEGIN
            UPDATE score_history 
            SET badge_earned = CASE 
                WHEN badge_earned = 'None' THEN '🏅 Veteran (Q' || NEW.quest_id || ')' 
                ELSE badge_earned || ', 🏅 Veteran (Q' || NEW.quest_id || ')' 
            END
            WHERE id = NEW.id;
        END;
    """)

    # Seed Default Sequential Quests
    cursor.execute("SELECT COUNT(*) FROM quests")
    if cursor.fetchone()[0] == 0:
        # Format: quest_id, title, creator_id, step, room_name, riddle, answer, reward
        q_data = [
            (1, "The Crypt of Whispers", None, 1, "Iron Gate", "I chill you to the bone. What am I?", "draft", "🗝️ Iron Key"),
            (1, "The Crypt of Whispers", None, 2, "Altar of Bones", "Count the skulls: 3 rows of 4, plus 2 hidden. How many?", "14", "📜 Scroll"),
            (1, "The Crypt of Whispers", None, 3, "Vault (EXIT)", "Sum of 10 + 15 * 2:", "40", "💎 Ruby"),

            (2, "The Sunken Vault", None, 1, "Sewer Grate", "I flow endlessly through dark tunnels. What am I?", "water", "💧 Flask"),
            (2, "The Sunken Vault", None, 2, "Aqueduct Core", "To stop the flooding, enter the boiling point of water in Celsius:", "100", "🔱 Trident Shard"),
            (2, "The Sunken Vault", None, 3, "Water Temple Altar (EXIT)", "Enter the number of sides on a triangle:", "3", "💠 Blue Pearl"),

            (3, "The Dragon's Lair", None, 1, "Obsidian Gates", "I melt under dragon breath but outlast steel in frost. What volcanic glass am I?", "obsidian", "💎 Black Gem"),
            (3, "The Dragon's Lair", None, 2, "Throne of Ashes", "To claim the crown, enter the final password: DRAGON", "dragon", "👑 Sovereign Crown"),
            (3, "The Dragon's Lair", None, 3, "The Molten Bridge (EXIT)", "Enter the temperature threshold in hundreds: 500 or ...?", "1000", "🔥 Flame Essence")
        ]
        
        cursor.executemany("""
            INSERT INTO quests 
            (quest_id, title, creator_id, step_number, room_name, riddle_text, correct_answer, item_reward) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, q_data)
        conn.commit()
    conn.close()

def register_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def get_all_quests():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT q.quest_id, q.title, u.username 
        FROM quests q 
        LEFT JOIN users u ON q.creator_id = u.id
    """)
    res = cursor.fetchall()
    conn.close()
    return res

def save_custom_quest(creator_id, title, riddles_list):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Dynamically find the next available quest_id
    cursor.execute("SELECT MAX(quest_id) FROM quests")
    max_id = cursor.fetchone()[0]
    new_quest_id = (max_id + 1) if max_id else 1
    
    for idx, riddle in enumerate(riddles_list, 1):
        room_name, riddle_text, answer, reward = riddle
        cursor.execute("""
            INSERT INTO quests (quest_id, title, creator_id, step_number, room_name, riddle_text, correct_answer, item_reward)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (new_quest_id, title, creator_id, idx, room_name, riddle_text, answer, reward))
    
    conn.commit()
    conn.close()

def setup_active_session(user_id, quest_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET active_quest_id = ?, current_step = 1, score = 100, inventory = 'None' 
        WHERE id = ?
    """, (quest_id, user_id))
    conn.commit()
    conn.close()

def get_player_state(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_quest_id, current_step, score, inventory FROM users WHERE id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_quest_length(quest_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(step_number) FROM quests WHERE quest_id = ?", (quest_id,))
    res = cursor.fetchone()[0]
    conn.close()
    return res if res else 0

def get_room_data(quest_id, step_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, room_name, riddle_text, correct_answer, item_reward 
        FROM quests 
        WHERE quest_id = ? AND step_number = ?
    """, (quest_id, step_number))
    row = cursor.fetchone()
    conn.close()
    return row

def get_user_badges(user_id):
    """Fetches all badges a user has earned directly from their score_history logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT badge_earned FROM score_history WHERE user_id = ? AND badge_earned != 'None'", (user_id,))
    
    badges = set()
    for row in cursor.fetchall():
        for b in row[0].split(','):
            if b.strip() and b.strip() != 'None':
                badges.add(b.strip())
                
    conn.close()
    return list(badges) if badges else ["None"]

def solve_riddle(user_id, current_step, current_score, current_inventory, item_reward, speed_bonus):
    conn = get_connection()
    cursor = conn.cursor()
    new_score = current_score + 150 + speed_bonus
    new_inv = item_reward if current_inventory == "None" else f"{current_inventory}, {item_reward}"
    new_step = current_step + 1
    
    cursor.execute("UPDATE users SET score = ?, inventory = ?, current_step = ? WHERE id = ?", 
                   (new_score, new_inv, new_step, user_id))
    conn.commit()
    conn.close()

def penalize_score(user_id, penalty_amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET score = MAX(0, score - ?) WHERE id = ?", (penalty_amount, user_id))
    conn.commit()
    conn.close()

def complete_quest(user_id, quest_id, score):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Inserting the score will automatically trigger the SQL Badges to be appended in Table 3
    cursor.execute("INSERT INTO score_history (user_id, quest_id, final_score) VALUES (?, ?, ?)", (user_id, quest_id, score))
    cursor.execute("UPDATE users SET active_quest_id = NULL, current_step = NULL WHERE id = ?", (user_id,))
    
    conn.commit()
    conn.close()

def get_top_scores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.username, 
            SUM(sh.final_score) as total_score, 
            GROUP_CONCAT(sh.badge_earned, ', ') as all_badges
        FROM score_history sh
        JOIN users u ON sh.user_id = u.id
        GROUP BY u.username
        ORDER BY total_score DESC LIMIT 10
    """)
    rows = cursor.fetchall()
    
    cleaned_rows = []
    for un, ts, badges_str in rows:
        if not badges_str: 
            badges = "None"
        else:
            b_set = set(b.strip() for b in badges_str.split(',') if b.strip() and b.strip() != 'None')
            badges = ", ".join(b_set) if b_set else "None"
        cleaned_rows.append((un, ts, badges))
        
    conn.close()
    return cleaned_rows