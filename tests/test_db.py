import os
import sqlite3
from backend.db import init_db, get_db_connection

def test_db_initialization():
    test_db_path = "test_data.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    init_db(test_db_path)
    assert os.path.exists(test_db_path)
    
    conn = get_db_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
    assert cursor.fetchone() is not None
    conn.close()
    os.remove(test_db_path)
