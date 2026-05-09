import time
import base64
from backend.db import get_db_connection
from backend.ai import generate_description_and_rating

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def process_next_image(prompt: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get one pending image
    cursor.execute("SELECT id, path FROM images WHERE status='Pending' LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False # No images pending
        
    img_id, path = row["id"], row["path"]
    
    # Mark as processing
    cursor.execute("UPDATE images SET status='Processing' WHERE id=?", (img_id,))
    conn.commit()
    
    try:
        base64_img = encode_image(path)
        result = generate_description_and_rating(base64_img, prompt)
        
        cursor.execute("UPDATE images SET status='Done', description=?, rating=? WHERE id=?", 
                       (result, result, img_id)) # We can split description/rating better later if needed
    except Exception as e:
        cursor.execute("UPDATE images SET status='Failed', description=? WHERE id=?", 
                       (str(e), img_id))
    
    conn.commit()
    conn.close()
    return True
