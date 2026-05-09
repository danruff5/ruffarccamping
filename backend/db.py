import sqlite3
import os

def init_db(db_path="data.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'Pending',
            description TEXT,
            rating TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection(db_path="data.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
