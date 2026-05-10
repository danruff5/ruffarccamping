import os
import sqlite3
import shutil
from difflib import SequenceMatcher
from PIL import Image
from jinja2 import Environment, FileSystemLoader

def filter_and_group_images(images, similarity_threshold=0.85):
    """
    Groups images by album (parent folder) and filters out duplicates.
    """
    albums = {}
    for img in images:
        # Extract album name from path
        album_name = os.path.basename(os.path.dirname(img["path"]))
        if not album_name:
            album_name = "Unsorted"
            
        if album_name not in albums:
            albums[album_name] = []
            
        # Deduplication logic
        is_duplicate = False
        if albums[album_name]:
            last_img = albums[album_name][-1]
            similarity = SequenceMatcher(None, img["description"], last_img["description"]).ratio()
            if similarity > similarity_threshold:
                is_duplicate = True
                
        if not is_duplicate:
            albums[album_name].append(img)
            
    return albums

def get_cover_photo(album_path, approved_images):
    """
    Determines the cover photo for an album.
    """
    cover_names = ["cover.jpg", "cover.png", "cover.webp", "cover.jpeg"]
    for name in cover_names:
        potential_path = os.path.join(album_path, name)
        if os.path.exists(potential_path):
            return potential_path
            
    # Fallback to the first approved image
    if approved_images:
        return approved_images[0]["path"]
    return None

def process_image(src_path, dest_dir, album_slug, filename):
    """
    Optimizes images for the web. Creates a WebP thumbnail and copies the full-res original.
    Returns relative paths (to docs root) for (thumbnail, full_res).
    """
    # Create directories
    thumb_dir = os.path.join(dest_dir, "thumbnails")
    full_dir = os.path.join(dest_dir, "full")
    os.makedirs(thumb_dir, exist_ok=True)
    os.makedirs(full_dir, exist_ok=True)
    
    # Paths relative to docs root
    rel_base = os.path.join("assets", album_slug)
    rel_thumb = os.path.join(rel_base, "thumbnails", os.path.splitext(filename)[0] + ".webp")
    rel_full = os.path.join(rel_base, "full", filename)
    
    # Absolute paths for processing
    abs_thumb = os.path.join(thumb_dir, os.path.splitext(filename)[0] + ".webp")
    abs_full = os.path.join(full_dir, filename)
    
    # 1. Create Thumbnail
    with Image.open(src_path) as img:
        img.thumbnail((800, 800))
        img.save(abs_thumb, "WEBP", quality=80)
        
    # 2. Copy Full-Res
    shutil.copy2(src_path, abs_full)
    
    return rel_thumb, rel_full

def generate_site(db_path="data.db", out_dir="docs", templates_dir="templates"):
    # Placeholder for Task 5
    pass

if __name__ == "__main__":
    # Placeholder for Task 5
    pass
