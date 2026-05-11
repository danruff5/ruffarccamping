from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from backend.db import get_db_connection, init_db, migrate_db
import sqlite3
import os
import requests
from backend.ai import OLLAMA_URL, MODEL_NAME
from backend.worker import process_single_image

app = FastAPI()

# Global control flag
processing_active = False

# Ensure DB exists, then migrate to add any new columns
if not os.path.exists("data.db"):
    init_db()
else:
    conn = get_db_connection()
    conn.execute("UPDATE images SET status='Pending' WHERE status='Processing'")
    conn.commit()
    conn.close()

migrate_db()

class ImageRequest(BaseModel):
    paths: List[str]

@app.post("/api/images")
def add_images(request: ImageRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    added = 0
    
    extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
    
    for path in request.paths:
        paths_to_add = []
        if os.path.isdir(path):
            # Scan directory for images
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(extensions):
                        paths_to_add.append(os.path.join(root, file))
        else:
            paths_to_add.append(path)

        for p in paths_to_add:
            try:
                cursor.execute("INSERT INTO images (path) VALUES (?)", (p,))
                added += 1
            except sqlite3.IntegrityError:
                pass # Already exists
                
    conn.commit()
    conn.close()
    return {"added": added}

class ProcessRequest(BaseModel):
    pass  # Prompt is now embedded in the system

import concurrent.futures

def worker_loop():
    global processing_active
    max_workers = min(os.cpu_count() or 4, 8)  # Balance CPU usage for encoding vs API limits
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = set()
        
        while processing_active:
            # Keep the thread pool fed up to max_workers
            while len(futures) < max_workers and processing_active:
                conn = get_db_connection()
                cursor = conn.cursor()
                # Use immediate mode to prevent SQLite lock contention
                cursor.execute("BEGIN IMMEDIATE")
                cursor.execute("SELECT id, path FROM images WHERE status='Pending' LIMIT 1")
                row = cursor.fetchone()
                
                if not row:
                    conn.commit()
                    conn.close()
                    break  # No more pending images
                
                img_id, path = row["id"], row["path"]
                cursor.execute("UPDATE images SET status='Processing' WHERE id=?", (img_id,))
                conn.commit()
                conn.close()
                
                # Submit to thread pool
                futures.add(executor.submit(process_single_image, img_id, path))
            
            if not futures:
                # No pending images and no running threads, we are done
                processing_active = False
                break
                
            # Wait for at least one future to complete before checking DB again
            done, futures = concurrent.futures.wait(
                futures, 
                return_when=concurrent.futures.FIRST_COMPLETED, 
                timeout=1.0
            )

@app.post("/api/process")
def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    global processing_active
    if not processing_active:
        processing_active = True
        background_tasks.add_task(worker_loop)
        return {"message": "Processing started"}
    return {"message": "Already processing"}

@app.post("/api/stop")
def stop_processing():
    global processing_active
    processing_active = False
    return {"message": "Stop signal sent"}

@app.post("/api/clear")
def clear_queue():
    global processing_active
    processing_active = False
    conn = get_db_connection()
    conn.execute("DELETE FROM images")
    conn.commit()
    conn.close()
    return {"message": "Queue cleared"}

class DeleteByStatusRequest(BaseModel):
    status: str

@app.post("/api/delete-by-status")
def delete_by_status(request: DeleteByStatusRequest):
    global processing_active
    if request.status == "Processing":
        processing_active = False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM images WHERE status=?", (request.status,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return {"deleted": deleted}

class DeleteByFolderRequest(BaseModel):
    folder: str
    status: str = ""  # optional: filter by status too

@app.post("/api/delete-by-folder")
def delete_by_folder(request: DeleteByFolderRequest):
    global processing_active
    conn = get_db_connection()
    cursor = conn.cursor()
    folder = request.folder.replace("/", "\\")
    if request.status:
        cursor.execute("DELETE FROM images WHERE path LIKE ? AND status=?", (folder + "%", request.status))
    else:
        cursor.execute("DELETE FROM images WHERE path LIKE ?", (folder + "%",))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return {"deleted": deleted}

@app.post("/api/retry-failed")
def retry_failed():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE images SET status='Pending', description=NULL, rating=NULL WHERE status='Failed'")
    retried = cursor.rowcount
    conn.commit()
    conn.close()
    return {"retried": retried}

@app.get("/api/folders")
def get_folders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT path FROM images")
    rows = cursor.fetchall()
    # Extract unique parent directories
    folders = set()
    for row in rows:
        folder = os.path.dirname(row["path"])
        if folder:
            folders.add(folder)
    conn.close()
    return {"folders": sorted(folders)}

from typing import Optional

@app.get("/api/status")
def get_status(
    status_filter: Optional[str] = None, 
    folder_filter: Optional[str] = None, 
    rating_filter: Optional[str] = None,
    page: int = 1, 
    per_page: int = 50
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM images WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status=?"
        params.append(status_filter)
    if folder_filter:
        folder = folder_filter.replace("/", "\\")
        query += " AND path LIKE ?"
        params.append(folder + "%")
    if rating_filter:
        query += " AND rating LIKE ?"
        params.append("%" + rating_filter + "%")
    
    # Get total count for this filter
    count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    images = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"images": images, "total": total, "page": page, "pages": max(1, (total + per_page - 1) // per_page)}

@app.get("/api/health")
def check_health():
    health = {"ollama": "Offline", "model": "Missing", "error": None}
    try:
        base_url = OLLAMA_URL.replace("/generate", "/tags")
        response = requests.get(base_url, timeout=2)
        if response.status_code == 200:
            health["ollama"] = "Online"
            models = response.json().get("models", [])
            if any(MODEL_NAME in m["name"] for m in models):
                health["model"] = "Ready"
            else:
                health["model"] = f"Not Found (Pull {MODEL_NAME})"
    except Exception as e:
        health["error"] = str(e)
    return health

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) as count FROM images GROUP BY status")
    rows = cursor.fetchall()
    stats = {row["status"]: row["count"] for row in rows}
    # Ensure all statuses exist in the response
    for s in ["Pending", "Processing", "Done", "Failed"]:
        if s not in stats:
            stats[s] = 0
    conn.close()
    return stats

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/explorer")
def read_explorer():
    return FileResponse("frontend/explorer.html")

@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")
