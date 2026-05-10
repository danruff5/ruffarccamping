import pytest
import os
import sys

# Add current directory to path so we can import build_site
sys.path.append(os.getcwd())

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

def test_get_cover_photo(tmp_path):
    from build_site import get_cover_photo
    import os
    
    album_path = tmp_path / "trip1"
    album_path.mkdir()
    
    approved_images = [{"path": "trip1/img1.jpg"}]
    
    # Test fallback
    assert get_cover_photo(str(album_path), approved_images) == "trip1/img1.jpg"
    
    # Test explicit cover
    cover_file = album_path / "cover.jpg"
    cover_file.write_text("dummy")
    assert get_cover_photo(str(album_path), approved_images) == str(cover_file)

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
    assert full.endswith(".webp")
    assert "thumbnails" in thumb
    assert "full" in full

def test_generate_html(tmp_path):
    from build_site import generate_site
    import os
    import sqlite3
    
    # Create mock db
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE images (id INTEGER PRIMARY KEY, path TEXT, status TEXT, description TEXT, rating TEXT, score INTEGER, timestamp DATETIME)")
    # Create mock source image
    img_dir = tmp_path / "trip1"
    os.makedirs(img_dir, exist_ok=True)
    img_path = img_dir / "img1.jpg"
    from PIL import Image
    Image.new('RGB', (10, 10)).save(img_path)
    
    conn.execute("INSERT INTO images (path, status, description, rating, score, timestamp) VALUES (?, ?, ?, ?, ?, ?)", 
                 (str(img_path), "Done", "Sunset", "Good", 8, "2026-05-10 10:00:00"))
    conn.commit()
    conn.close()
    
    # generate_site takes an output directory
    generate_site(db_path=str(db_path), out_dir=str(tmp_path / "docs"), templates_dir="templates")
    
    assert os.path.exists(tmp_path / "docs" / "index.html")
    assert os.path.exists(tmp_path / "docs" / "albums" / "trip1.html")
