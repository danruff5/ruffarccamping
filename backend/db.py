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
    if "dhash" not in existing_cols:
        cursor.execute("ALTER TABLE images ADD COLUMN dhash TEXT")
        print("[DB] Migrated: added 'dhash' column")

    conn.commit()
    conn.close()

from backend.hash_utils import calculate_dhash

def populate_missing_hashes(db_path="data.db"):
    """
    Scans the database for processed images lacking a dHash,
    calculates them, prints progress log, and updates in batches.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM images WHERE status='Done' AND dhash IS NULL")
    total = cursor.fetchone()["total"]
    
    if total == 0:
        conn.close()
        return
        
    print(f"[DB Migration] Found {total} existing images without dhash. Starting hashing...")
    
    cursor.execute("SELECT id, path FROM images WHERE status='Done' AND dhash IS NULL")
    rows = cursor.fetchall()
    
    updated = 0
    for idx, row in enumerate(rows):
        img_id, path = row["id"], row["path"]
        if os.path.exists(path):
            try:
                h = calculate_dhash(path)
                cursor.execute("UPDATE images SET dhash=? WHERE id=?", (h, img_id))
                updated += 1
            except Exception as e:
                print(f"[DB Migration] Failed to hash {path}: {e}")
                
        # Commit in batches of 50 and print progress
        if (idx + 1) % 50 == 0 or (idx + 1) == total:
            conn.commit()
            print(f"[DB Migration] Progress: Hashed {idx + 1}/{total} images...")
            
    if updated > 0:
        conn.commit()
        print(f"[DB Migration] Completed hashing: populated dhash for {updated} images")
    conn.close()

def get_db_connection(db_path="data.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
