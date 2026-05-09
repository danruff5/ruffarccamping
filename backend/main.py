from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from backend.db import get_db_connection, init_db
import sqlite3
import os
from backend.worker import process_next_image

app = FastAPI()

# Ensure DB exists
if not os.path.exists("data.db"):
    init_db()

class ImageRequest(BaseModel):
    paths: List[str]

@app.post("/api/images")
def add_images(request: ImageRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    added = 0
    for path in request.paths:
        try:
            cursor.execute("INSERT INTO images (path) VALUES (?)", (path,))
            added += 1
        except sqlite3.IntegrityError:
            pass # Already exists
    conn.commit()
    conn.close()
    return {"added": added}

class ProcessRequest(BaseModel):
    prompt: str

def worker_loop(prompt: str):
    while process_next_image(prompt):
        pass # Keep processing until queue is empty

@app.post("/api/process")
def start_processing(request: ProcessRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(worker_loop, request.prompt)
    return {"message": "Processing started in background"}

@app.get("/api/status")
def get_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM images ORDER BY id DESC LIMIT 100")
    images = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"images": images}

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")
