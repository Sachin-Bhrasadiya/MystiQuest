import random
import sqlite3

DB_NAME = "dungeon_quest_opt.db"

def get_connection():
    """Returns a new SQLite database connection."""
    return sqlite3.connect(DB_NAME)

def init_database():
    """Initializes optimized 4-table SQLite database and seeds official quests."""
    conn = get_connection()
    cursor = conn.cursor()

    # Optimized Users table now tracks all game state directly!
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            active_quest_id INTEGER,
            score INTEGER DEFAULT 100,
            clues_found INTEGER DEFAULT 0,
            inventory TEXT DEFAULT 'None',
            clue_sequence TEXT,
            FOREIGN KEY (active_quest_id) REFERENCES quests(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_title TEXT,
            case_name TEXT,
            is_custom BOOLEAN DEFAULT 0,
            creator_username TEXT DEFAULT 'System'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quest_id INTEGER,
            location_name TEXT,
            riddle_text TEXT,
            correct_answer TEXT,
            item_reward TEXT,
            FOREIGN KEY (quest_id) REFERENCES quests(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quest_id INTEGER,
            final_score INTEGER,
            date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (quest_id) REFERENCES quests(id)
        )
    """)

    # Seed initial official quests if empty
    cursor.execute("SELECT COUNT(*) FROM quests WHERE is_custom = 0")
    if cursor.fetchone()[0] == 0:
        quests_data = [
            ("The Crypt of Whispers", "Catacombs of Ash"),
            ("The Sunken Vault", "Flooded Dungeons"),
            ("The Dragon's Lair", "Obsidian Keep")
        ]
        
        for q_title, q_loc in quests_data:
            cursor.execute("INSERT INTO quests (quest_title, case_name, is_custom, creator_username) VALUES (?, ?, 0, 'System')", (q_title, q_loc))
            q_id = cursor.lastrowid

            if q_title == "The Crypt of Whispers":
                clues = [
                    ("The Iron Gate", 'Riddle: "I have no breath, yet I chill you to the bone. I sweep through stone halls when torches die out. What am I?"', "draft", "🗝️ Iron Key"),
                    ("The Altar of Bones", 'Riddle: "Count the skulls upon the altar: 3 rows of 4, plus 2 hidden in the shadows. How many?"', "14", "📜 Scroll of Wards"),
                    ("The Crypt Master's Tomb", 'Riddle: "To break the ancient seal, speak the word of awakening written on the tomb: REST"', "rest", "🛡️ Ancient Shield"),
                    ("The Executioner's Pit", 'Riddle: "I hang by a single rope above the dark chasm and swing back and forth. What am I?"', "pendulum", "🪓 Iron Axe"),
                    ("The Secret Vault Door", 'Riddle: "To unlock the heavy stone deadbolt, enter the sum of 10 + 15 * 2:"', "40", "💎 Ruby Gem")
                ]
            elif q_title == "The Sunken Vault":
                clues = [
                    ("Sewer Grate", 'Riddle: "I flow endlessly through dark tunnels, reflecting no stars. What dark liquid am I?"', "water", "💧 Flask"),
                    ("Sunken Library", 'Riddle: "Water ruined the parchment, but the numerical vault code remains visible: 707"', "707", "📜 Waterlogged Tome"),
                    ("Aqueduct Core", 'Riddle: "To stop the flooding, enter the boiling point of water in Celsius:"', "100", "🔱 Trident Shard"),
                    ("The Flooded Bridge", 'Riddle: "I have four legs when young, two in maturity, but here I swim with fins. What am I?"', "fish", "🐟 Scale"),
                    ("Water Temple Altar", 'Riddle: "To drain the basin, enter the number of sides on a triangle:"', "3", "💠 Blue Pearl")
                ]
            else:
                clues = [
                    ("Obsidian Gates", 'Riddle: "I melt under dragon breath but outlast steel in the frost. What black volcanic glass am I?"', "obsidian", "💎 Black Gem"),
                    ("Hoard Chamber", 'Riddle: "Count the gold coins stacked: 50 piled high, 20 scattered. Total:"', "70", "💰 Dragon Coin"),
                    ("Throne of Ashes", 'Riddle: "To claim the crown, enter the final password of the realm: DRAGON"', "dragon", "👑 Sovereign Crown"),
                    ("Dragon's Nursery", 'Riddle: "I am born from fire wrapped in hard shell. What am I?"', "egg", "🥚 Dragon Egg"),
                    ("The Molten Bridge", 'Riddle: "To cross the lava river safely, enter the temperature threshold in hundreds: 500 or ...?"', "1000", "🔥 Flame Essence")
                ]

            for loc, ridd, ans, rew in clues:
                cursor.execute("INSERT INTO clues (quest_id, location_name, riddle_text, correct_answer, item_reward) VALUES (?, ?, ?, ?, ?)",
                               (q_id, loc, ridd, ans, rew))

        conn.commit()
    conn.close()

def register_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def get_all_quests():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, quest_title, case_name, creator_username FROM quests")
    quests = cursor.fetchall()
    conn.close()
    return quests

def create_custom_quest(title, zone, creator, clues_list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quests (quest_title, case_name, is_custom, creator_username) VALUES (?, ?, 1, ?)",
                   (title, zone, creator))
    new_quest_id = cursor.lastrowid

    for idx, (r, a) in enumerate(clues_list, start=1):
        cursor.execute("INSERT INTO clues (quest_id, location_name, riddle_text, correct_answer, item_reward) VALUES (?, ?, ?, ?, ?)",
                       (new_quest_id, f"Chamber {idx}", r, a, "🏆 Custom Relic"))
    conn.commit()
    conn.close()

def setup_active_session(user_id, quest_id):
    """Sets up a new active session using the optimized sequence string."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM clues WHERE quest_id = ?", (quest_id,))
    clue_ids = [str(row[0]) for row in cursor.fetchall()]
    random.shuffle(clue_ids)
    sequence_string = ",".join(clue_ids)

    cursor.execute("""
        UPDATE users 
        SET active_quest_id = ?, score = 100, clues_found = 0, 
            inventory = 'None', clue_sequence = ?
        WHERE id = ?
    """, (quest_id, sequence_string, user_id))
    
    conn.commit()
    conn.close()

def get_player_progress(user_id):
    """Fetches user progress and sequence string from users table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_quest_id, score, clues_found, inventory, clue_sequence FROM users WHERE id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def get_quest_title(quest_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quest_title FROM quests WHERE id = ?", (quest_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else ""

def get_current_clue(user_id):
    """Parses sequence string and fetches current clue based on clues_found."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT clues_found, clue_sequence FROM users WHERE id = ?", (user_id,))
    res = cursor.fetchone()
    if not res or not res[1]:
        conn.close()
        return None
    
    clues_found, sequence_string = res
    sequence_list = sequence_string.split(",")
    
    if clues_found >= len(sequence_list):
        conn.close()
        return None
        
    current_clue_id = int(sequence_list[clues_found])
    
    cursor.execute("SELECT id, location_name, riddle_text, correct_answer, item_reward FROM clues WHERE id = ?", (current_clue_id,))
    clue = cursor.fetchone()
    conn.close()
    return clue

def update_player_progress(user_id, new_score, new_clues_found, new_inventory):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET score = ?, clues_found = ?, inventory = ? 
        WHERE id = ?
    """, (new_score, new_clues_found, new_inventory, user_id))
    conn.commit()
    conn.close()

def update_player_score(user_id, new_score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET score = ? WHERE id = ?", (new_score, user_id))
    conn.commit()
    conn.close()

def save_score_history(user_id, quest_id, score):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO score_history (user_id, quest_id, final_score) VALUES (?, ?, ?)", (user_id, quest_id, score))
    conn.commit()
    conn.close()

def get_top_scores():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, q.quest_title, sh.final_score, sh.date_played 
        FROM score_history sh
        JOIN users u ON sh.user_id = u.id
        JOIN quests q ON sh.quest_id = q.id
        ORDER BY sh.final_score DESC, sh.date_played ASC
        LIMIT 10
    """)
    res = cursor.fetchall()
    conn.close()
    return res