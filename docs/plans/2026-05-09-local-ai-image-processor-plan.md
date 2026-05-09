# Local AI Image Processor Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** A self-hosted web application that leverages local CUDA-accelerated Vision Language Models to process large batches of images, generating subjective ratings and descriptions stored in a SQLite database.

**Architecture:** Python FastAPI backend with a SQLite database to queue image processing. A background worker picks up images and sends them to a local Ollama instance for rating, while a vanilla HTML/JS web dashboard polls the backend to display real-time progress.

**Tech Stack:** Python 3.10+, FastAPI, SQLite (builtin), Ollama, HTML/JS/TailwindCSS.

---

### Task 1: Environment Setup

**Files:**
- Create: `requirements.txt`

**Step 1: Write `requirements.txt`**

```text
fastapi==0.110.0
uvicorn==0.28.0
requests==2.31.0
pytest==8.1.1
httpx==0.27.0
```

**Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: PASS with "Successfully installed..."

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: setup project dependencies"
```

---

### Task 2: Database Setup

**Files:**
- Create: `backend/db.py`
- Create: `tests/test_db.py`

**Step 1: Write the failing test**

```python
# tests/test_db.py
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'backend'"

**Step 3: Write minimal implementation**

```python
# backend/db.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/db.py tests/test_db.py
git commit -m "feat: initialize sqlite database schema"
```

---

### Task 3: API Endpoints (Images Queue)

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing test**

```python
# tests/test_main.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_add_images():
    response = client.post("/api/images", json={"paths": ["img1.png", "img2.png"]})
    assert response.status_code == 200
    assert response.json()["added"] == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'backend.main'"

**Step 3: Write minimal implementation**

```python
# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from backend.db import get_db_connection, init_db
import sqlite3
import os

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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: add api endpoint to queue images"
```

---

### Task 4: AI Engine Integration

**Files:**
- Create: `backend/ai.py`
- Create: `tests/test_ai.py`

**Step 1: Write the failing test**

```python
# tests/test_ai.py
from backend.ai import generate_description_and_rating
import base64

def test_generate_description_mock(monkeypatch):
    # Mock requests.post to avoid needing real Ollama in tests
    class MockResponse:
        def json(self):
            return {"response": "A nice dog. Rating: 8/10"}
    
    def mock_post(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr("requests.post", mock_post)
    
    result = generate_description_and_rating("mock_base64_image", "Describe this")
    assert "A nice dog" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ai.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'backend.ai'"

**Step 3: Write minimal implementation**

```python
# backend/ai.py
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llava:7b" # Or moondream

def generate_description_and_rating(base64_image: str, prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "images": [base64_image],
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json().get("response", "")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ai.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/ai.py tests/test_ai.py
git commit -m "feat: integrate ollama local vision model api"
```

---

### Task 5: Background Processing Worker

**Files:**
- Create: `backend/worker.py`
- Modify: `backend/main.py`

**Step 1: Write minimal implementation for worker**

```python
# backend/worker.py
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
```

**Step 2: Add trigger endpoint to API**

```python
# Add to backend/main.py
from fastapi import BackgroundTasks
from backend.worker import process_next_image

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
```

**Step 3: Commit**

```bash
git add backend/worker.py backend/main.py
git commit -m "feat: add background worker to process images"
```

---

### Task 6: Basic Frontend Dashboard

**Files:**
- Create: `frontend/index.html`
- Modify: `backend/main.py` (to serve static files)

**Step 1: Write minimal HTML implementation**

```html
<!-- frontend/index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>AI Image Processor</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-4xl mx-auto bg-white p-6 rounded shadow">
        <h1 class="text-2xl font-bold mb-4">Local AI Image Processor</h1>
        
        <div class="mb-4">
            <h2 class="text-xl">1. Queue Images</h2>
            <input type="text" id="img-path" placeholder="C:/images/pic1.jpg" class="border p-2 w-full mb-2">
            <button onclick="addImages()" class="bg-blue-500 text-white px-4 py-2 rounded">Add to Queue</button>
        </div>
        
        <div class="mb-4">
            <h2 class="text-xl">2. Process Queue</h2>
            <input type="text" id="prompt" placeholder="Describe the image and rate its quality 1-10" class="border p-2 w-full mb-2">
            <button onclick="startProcessing()" class="bg-green-500 text-white px-4 py-2 rounded">Start AI Processing</button>
        </div>

        <div>
            <h2 class="text-xl">3. Results</h2>
            <button onclick="fetchStatus()" class="bg-gray-500 text-white px-4 py-2 rounded mb-2">Refresh Status</button>
            <div id="results" class="space-y-2 mt-4"></div>
        </div>
    </div>

    <script>
        async function addImages() {
            const path = document.getElementById('img-path').value;
            await fetch('/api/images', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({paths: [path]})
            });
            alert('Added!');
            fetchStatus();
        }

        async function startProcessing() {
            const prompt = document.getElementById('prompt').value;
            await fetch('/api/process', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: prompt})
            });
            alert('Started background processing!');
        }

        async function fetchStatus() {
            const res = await fetch('/api/status');
            const data = await res.json();
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = data.images.map(img => `
                <div class="border p-2 rounded">
                    <strong>${img.path}</strong> - <span class="text-blue-600">${img.status}</span>
                    <p class="text-sm mt-1 text-gray-600">${img.description || ''}</p>
                </div>
            `).join('');
        }
        
        // Auto-refresh every 5 seconds
        setInterval(fetchStatus, 5000);
        fetchStatus();
    </script>
</body>
</html>
```

**Step 2: Update FastAPI to serve frontend**

```python
# Add to top of backend/main.py
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Add at bottom of backend/main.py
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")
```

**Step 3: Run the server and check manually**

Run: `uvicorn backend.main:app --reload`
Expected: Server runs without errors.

**Step 4: Commit**

```bash
git add frontend/index.html backend/main.py
git commit -m "feat: add frontend dashboard"
```
