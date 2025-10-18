import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("support.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            department TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_request(user_id, username, message, department):
    conn = sqlite3.connect("support.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO requests (user_id, username, message, department, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, message, department, datetime.now().isoformat()))
    conn.commit()
    conn.close()
