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
    assert "thumbnails" in thumb
