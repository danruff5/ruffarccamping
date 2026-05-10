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
            rating TEXT,
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_response TEXT
        )
    ''')
    conn.commit()
    conn.close()

def migrate_db(db_path="data.db"):
    """Add new columns to existing databases without losing data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(images)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    if "score" not in existing_cols:
        cursor.execute("ALTER TABLE images ADD COLUMN score INTEGER")
        print("[DB] Migrated: added 'score' column")
    if "timestamp" not in existing_cols:
        cursor.execute("ALTER TABLE images ADD COLUMN timestamp DATETIME")
        print("[DB] Migrated: added 'timestamp' column")
    if "raw_response" not in existing_cols:
        cursor.execute("ALTER TABLE images ADD COLUMN raw_response TEXT")
        print("[DB] Migrated: added 'raw_response' column")

    conn.commit()
    conn.close()

def get_db_connection(db_path="data.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
