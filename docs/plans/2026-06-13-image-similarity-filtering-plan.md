# Image Similarity Filtering Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Implement dHash perceptual hashing to identify visually similar photos and select the best one based on AI score for the static site gallery.

**Architecture:** Add a `dhash` column to the DB. Compute dHash when images are processed. Run a streaming leader election in `build_site.py` based on Hamming distance and image score.

**Tech Stack:** Python, Pillow, SQLite, pytest.

---

### Task 1: Hash Utils and Tests

**Files:**
- Create: `backend/hash_utils.py`
- Create: `tests/test_hash_utils.py`

**Step 1: Write the failing tests**

Create `tests/test_hash_utils.py`:
```python
import pytest
from PIL import Image
from backend.hash_utils import calculate_dhash, hamming_distance

def test_hamming_distance():
    assert hamming_distance("0000000000000000", "0000000000000000") == 0
    assert hamming_distance("ffffffffffffffff", "0000000000000000") == 64
    assert hamming_distance("0f0f0f0f0f0f0f0f", "f0f0f0f0f0f0f0f0") == 64
    assert hamming_distance("1111111111111111", "0111111111111111") == 3

def test_dhash_calculation():
    # Create two identical images and one different
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="red")
    img3 = Image.new("RGB", (100, 100), color="blue")
    
    h1 = calculate_dhash(img1)
    h2 = calculate_dhash(img2)
    h3 = calculate_dhash(img3)
    
    assert len(h1) == 16
    assert h1 == h2
    assert hamming_distance(h1, h3) > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_hash_utils.py`
Expected: FAIL (Module not found / functions not defined)

**Step 3: Write implementation**

Create `backend/hash_utils.py`:
```python
from PIL import Image

def calculate_dhash(image_path_or_pil_img) -> str:
    """
    Computes a 64-bit difference hash (dHash) for an image.
    Returns a 16-character hexadecimal string representation.
    """
    if isinstance(image_path_or_pil_img, str):
        img = Image.open(image_path_or_pil_img)
    else:
        img = image_path_or_pil_img
        
    # Convert to grayscale and resize to 9x8
    img = img.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
    pixels = list(img.getdata())
    
    # Compute difference between adjacent pixels in a row
    difference = []
    for row in range(8):
        for col in range(8):
            pixel_left = pixels[row * 9 + col]
            pixel_right = pixels[row * 9 + col + 1]
            difference.append(pixel_left > pixel_right)
            
    # Convert binary list to hex string
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2**(index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].zfill(2))
            decimal_value = 0
            
    return "".join(hex_string)

def hamming_distance(h1: str, h2: str) -> int:
    """
    Computes the Hamming distance between two 16-character hex dHashes.
    """
    if not h1 or not h2:
        return 999
    try:
        return (int(h1, 16) ^ int(h2, 16)).bit_count()
    except ValueError:
        return 999
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_hash_utils.py`
Expected: PASS

**Step 5: Commit**

Run:
```bash
git add backend/hash_utils.py tests/test_hash_utils.py ; git commit -m "feat: implement dhash calculation and helper utilities"
```

---

### Task 2: DB Schema Migration and Auto-population with Progress Tracking

**Files:**
- Modify: `backend/db.py:22-41`
- Modify: `backend/main.py:18-28`
- Modify: `tests/test_db.py`

**Step 1: Write test for db migration**

Modify `tests/test_db.py` to check that the `dhash` column is created after initialization/migration:
```python
import sqlite3
import os
from backend.db import init_db, migrate_db, get_db_connection

def test_db_migration(tmp_path):
    db_file = str(tmp_path / "test_data.db")
    init_db(db_file)
    migrate_db(db_file)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(images)")
    cols = {row[1] for row in cursor.fetchall()}
    conn.close()
    
    assert "dhash" in cols
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db.py`
Expected: FAIL (AssertionError: 'dhash' not in cols)

**Step 3: Implement migration and existing image population**

1. Modify `backend/db.py`'s `migrate_db` function to add `dhash TEXT`:
```python
    if "dhash" not in existing_cols:
        cursor.execute("ALTER TABLE images ADD COLUMN dhash TEXT")
        print("[DB] Migrated: added 'dhash' column")
```

2. Add a background migration script inside `backend/db.py` to populate missing dhashes with progressive logs and batch commits:
```python
from backend.hash_utils import calculate_dhash

def populate_missing_hashes(db_path="data.db"):
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
```

3. Call `populate_missing_hashes` in `backend/main.py` right after migration:
```python
migrate_db()
from backend.db import populate_missing_hashes
populate_missing_hashes()
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db.py`
Expected: PASS

**Step 5: Commit**

Run:
```bash
git add backend/db.py backend/main.py tests/test_db.py ; git commit -m "feat: add dhash schema migration and auto-populate existing images"
```

---

### Task 3: Worker Integration

**Files:**
- Modify: `backend/worker.py:55-63`

**Step 1: Run pytest to see existing tests pass**

Run: `python -m pytest tests/test_ai.py`
Expected: PASS

**Step 2: Implement dhash computation in worker**

Modify `backend/worker.py` in `process_single_image`:
```python
        base64_img = encode_image(path)
        
        # Calculate dhash using the PIL Image directly before closing/encoding or re-open
        from backend.hash_utils import calculate_dhash
        dhash_val = calculate_dhash(path)

        t_ai = time.time()
        result = generate_description_and_rating(base64_img)
```
And save it to the DB:
```python
        cursor.execute(
            "UPDATE images SET status='Done', description=?, rating=?, score=?, timestamp=CURRENT_TIMESTAMP, raw_response=?, dhash=? WHERE id=?",
            (photo_desc, full_critique, score, raw, dhash_val, img_id)
        )
```

**Step 3: Run pytest to verify everything compiles and passes**

Run: `python -m pytest tests/test_ai.py`
Expected: PASS

**Step 4: Commit**

Run:
```bash
git add backend/worker.py ; git commit -m "feat: calculate and store dhash in background worker"
```

---

### Task 4: Static Site Builder Election Filter

**Files:**
- Modify: `build_site.py:11-37`
- Modify: `tests/test_build_site.py`

**Step 1: Write test for selection and clustering**

Modify `tests/test_build_site.py` to check that the streaming election selects the highest scoring photo in a similar group:
```python
from build_site import filter_and_group_images

def test_similarity_leader_election():
    mock_images = [
        # Album 1: similar photos
        {"path": "album1/img1.jpg", "description": "A cat on a mat", "dhash": "0000000000000000", "score": 7},
        {"path": "album1/img2.jpg", "description": "A cat on a mat", "dhash": "0000000000000001", "score": 9},  # best
        {"path": "album1/img3.jpg", "description": "A cat on a mat", "dhash": "0000000000000003", "score": 8},
        
        # Different photo
        {"path": "album1/img4.jpg", "description": "A dog on a rug", "dhash": "ffffffffffffffff", "score": 7},
    ]
    
    albums = filter_and_group_images(mock_images)
    photos = albums["album1"]
    
    assert len(photos) == 2
    # The best one out of the similar group is chosen
    assert photos[0]["path"] == "album1/img2.jpg"
    assert photos[1]["path"] == "album1/img4.jpg"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_build_site.py`
Expected: FAIL (img2 is not correctly selected or duplicates remain)

**Step 3: Implement streaming leader-election in `build_site.py`**

Replace `filter_and_group_images` in `build_site.py`:
```python
from backend.hash_utils import hamming_distance
from difflib import SequenceMatcher

def filter_and_group_images(images, similarity_threshold=0.85):
    """
    Groups images by album (parent folder) and filters out duplicates,
    keeping only the one with the highest score in any cluster of similar images.
    """
    albums = {}
    
    # 1. Group images by album first
    album_groups = {}
    for img in images:
        album_name = os.path.basename(os.path.dirname(img["path"]))
        if not album_name:
            album_name = "Unsorted"
        if album_name not in album_groups:
            album_groups[album_name] = []
        album_groups[album_name].append(img)
        
    # 2. Run streaming leader-election per album
    for album_name, photos in album_groups.items():
        albums[album_name] = []
        if not photos:
            continue
            
        leader = photos[0]
        
        for next_photo in photos[1:]:
            # Determine similarity
            is_similar = False
            
            h1, h2 = leader.get("dhash"), next_photo.get("dhash")
            if h1 and h2:
                # Use perceptual hash similarity
                dist = hamming_distance(h1, h2)
                is_similar = (dist <= 10)
            else:
                # Fall back to description string similarity
                sim_ratio = SequenceMatcher(None, leader.get("description", ""), next_photo.get("description", "")).ratio()
                is_similar = (sim_ratio > similarity_threshold)
                
            if is_similar:
                # Same visual group: keep the one with the higher score
                leader_score = leader.get("score") or 0
                next_score = next_photo.get("score") or 0
                if next_score > leader_score:
                    leader = next_photo
            else:
                # Different visual group: finalize current leader and elect new one
                albums[album_name].append(leader)
                leader = next_photo
                
        # Finalize the last remaining leader
        albums[album_name].append(leader)
        
    return albums
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_build_site.py`
Expected: PASS

**Step 5: Commit**

Run:
```bash
git add build_site.py tests/test_build_site.py ; git commit -m "feat: implement streaming leader election for similarity filtering in build_site"
```
