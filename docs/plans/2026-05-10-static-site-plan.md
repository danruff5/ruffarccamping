# Static Site Generator Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Build a Python script that generates a static HTML photo gallery from a local SQLite database, filtering by rating and description similarity, and optimizing images.

**Architecture:** A standalone `build_site.py` script queries the `images` table in `data.db`, groups by album, filters duplicates using `difflib`, generates WebP thumbnails using `Pillow`, and renders static HTML into a `docs/` folder using `Jinja2` templates.

**Tech Stack:** Python, sqlite3, Jinja2, Pillow.

---

### Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Write the failing test**

Run: `python -c "import jinja2; import PIL"`
Expected: FAIL with ModuleNotFoundError or ImportError

**Step 2: Add dependencies to requirements.txt**

Append `Jinja2` and `Pillow` to `requirements.txt`.

**Step 3: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: PASS

**Step 4: Run test to verify it passes**

Run: `python -c "import jinja2; import PIL"`
Expected: PASS without output

**Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore: add Jinja2 and Pillow dependencies"
```

### Task 2: Create Template Files

**Files:**
- Create: `templates/base.html`
- Create: `templates/index.html`
- Create: `templates/album.html`

**Step 1: Write the base layout template**
Create `templates/base.html` with a basic dark mode CSS grid layout, including standard `<html>`, `<head>`, and `<body>` tags. Include CSS block for custom styling.

**Step 2: Write the index template**
Create `templates/index.html` extending `base.html` to display a grid of albums. It should loop through an `albums` variable.

**Step 3: Write the album template**
Create `templates/album.html` extending `base.html` to display a masonry layout of photos with a modal for full-res view. It should loop through a `photos` variable.

**Step 4: Commit**
```bash
git add templates/
git commit -m "feat: add Jinja2 templates for static site"
```

### Task 3: Implement Database and Filtering Logic

**Files:**
- Create: `tests/test_build_site.py`
- Create: `build_site.py`

**Step 1: Write the failing test for filtering**

```python
# in tests/test_build_site.py
def test_filter_and_group_images():
    from build_site import filter_and_group_images
    mock_images = [
        {"path": "trip1/img1.jpg", "score": 8, "description": "A beautiful sunset over the mountains", "timestamp": "2026-05-10T10:00:00Z"},
        {"path": "trip1/img2.jpg", "score": 9, "description": "A beautiful sunset over the mountains", "timestamp": "2026-05-10T10:01:00Z"},
        {"path": "trip1/img3.jpg", "score": 7, "description": "A campfire at night", "timestamp": "2026-05-10T11:00:00Z"},
        {"path": "trip2/img4.jpg", "score": 8, "description": "Hiking the trail", "timestamp": "2026-05-11T09:00:00Z"},
    ]
    # filter_and_group_images should return a dict: {"trip1": [img1, img3], "trip2": [img4]}
    # Notice img2 is dropped due to similar description to img1
    result = filter_and_group_images(mock_images, similarity_threshold=0.85)
    
    assert "trip1" in result
    assert "trip2" in result
    assert len(result["trip1"]) == 2
    assert result["trip1"][0]["path"] == "trip1/img1.jpg"
    assert result["trip1"][1]["path"] == "trip1/img3.jpg"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_site.py -v`
Expected: FAIL (ImportError for `filter_and_group_images`)

**Step 3: Write minimal implementation**

Implement `filter_and_group_images` in `build_site.py` using `difflib.SequenceMatcher`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_site.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_build_site.py build_site.py
git commit -m "feat: add database filtering and grouping logic"
```

### Task 4: Implement Image Processing Logic

**Files:**
- Modify: `tests/test_build_site.py`
- Modify: `build_site.py`

**Step 1: Write the failing test for image optimization**

```python
# in tests/test_build_site.py
def test_process_image(tmp_path):
    from build_site import process_image
    from PIL import Image
    import os
    
    # Create a dummy image
    src_img = tmp_path / "test.jpg"
    img = Image.new('RGB', (1000, 1000), color = 'red')
    img.save(src_img)
    
    dest_dir = tmp_path / "docs" / "assets" / "trip1"
    
    # process_image should return (thumbnail_path, full_res_path) relative to docs/
    thumb, full = process_image(str(src_img), str(dest_dir), "trip1", "test.jpg")
    
    assert os.path.exists(tmp_path / "docs" / thumb)
    assert os.path.exists(tmp_path / "docs" / full)
    assert thumb.endswith(".webp")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_site.py::test_process_image -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement `process_image` in `build_site.py` using Pillow to resize, save as `.webp`, and copy the original image.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_site.py::test_process_image -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_build_site.py build_site.py
git commit -m "feat: add Pillow-based image resizing and WebP generation"
```

### Task 5: Implement HTML Generation and Main Build Flow

**Files:**
- Modify: `tests/test_build_site.py`
- Modify: `build_site.py`

**Step 1: Write the failing test for HTML generation**

Add a simple test for `generate_html()` ensuring Jinja2 properly renders output. (Or skip the direct unit test for HTML output and test it manually, but following TDD, we test that files are written).

```python
# in tests/test_build_site.py
def test_generate_html(tmp_path):
    from build_site import generate_site
    import os
    
    # generate_site takes an output directory
    generate_site(db_path=":memory:", out_dir=str(tmp_path), templates_dir="templates")
    
    assert os.path.exists(tmp_path / "index.html")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_build_site.py::test_generate_html -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Implement `generate_site` in `build_site.py` connecting the DB query (sqlite3), filtering, image processing, and Jinja2 rendering.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_build_site.py::test_generate_html -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_build_site.py build_site.py
git commit -m "feat: complete static site generator flow and HTML rendering"
```
