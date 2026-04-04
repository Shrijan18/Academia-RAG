import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    # Connects to users.db (creates it if it doesn't exist)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create the Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Data for your 1 Admin and 8 Teachers
    accounts = [
        ("admin_bit", "admin123", "admin"),
        ("teacher_it_01", "bit_teach2026", "teacher"),
        ("teacher_it_02", "bit_teach2026", "teacher"),
        ("teacher_it_03", "bit_teach2026", "teacher"),
        # ... add more as needed
    ]

    for username, password, role in accounts:
        hashed_pw = generate_password_hash(password)
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                           (username, hashed_pw, role))
        except sqlite3.IntegrityError:
            print(f"User {username} already exists.")

    conn.commit()
    conn.close()
    print("✅ Database initialized with Admin and Teacher accounts.")

if __name__ == "__main__":
    init_db()