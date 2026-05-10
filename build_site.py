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
    Optimizes images for the web. Creates a WebP thumbnail (800px) and an
    optimized full-size WebP (2048px) for the lightbox view.
    Skips processing if both output files already exist (incremental build).
    Returns relative paths (to docs root) for (thumbnail, full_res).
    """
    # Create directories
    thumb_dir = os.path.join(dest_dir, "thumbnails")
    full_dir = os.path.join(dest_dir, "full")
    os.makedirs(thumb_dir, exist_ok=True)
    os.makedirs(full_dir, exist_ok=True)
    
    # Both outputs are WebP
    base_name = os.path.splitext(filename)[0] + ".webp"
    
    # Paths relative to docs root
    rel_base = os.path.join("assets", album_slug)
    rel_thumb = os.path.join(rel_base, "thumbnails", base_name)
    rel_full = os.path.join(rel_base, "full", base_name)
    
    # Absolute paths for processing
    abs_thumb = os.path.join(thumb_dir, base_name)
    abs_full = os.path.join(full_dir, base_name)
    
    # Skip if already processed (incremental build)
    if os.path.exists(abs_thumb) and os.path.exists(abs_full):
        return rel_thumb, rel_full

    # 1. Create Thumbnail (max 800px, quality 80)
    with Image.open(src_path) as img:
        img.thumbnail((800, 800))
        img.save(abs_thumb, "WEBP", quality=80)
        
    # 2. Create optimized full-size (max 2048px, quality 90)
    with Image.open(src_path) as img:
        img.thumbnail((2048, 2048))
        img.save(abs_full, "WEBP", quality=90)
    
    return rel_thumb, rel_full

def generate_site(db_path="data.db", out_dir="docs", templates_dir="templates"):
    """
    Main flow to generate the static site.
    """
    if not os.path.exists(db_path) and db_path != ":memory:":
        print(f"Error: Database not found at {db_path}")
        return

    # 1. Setup Directories — preserve existing albums/assets for incremental builds
    os.makedirs(os.path.join(out_dir, "albums"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    
    # 2. Fetch Data from DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM images WHERE status='Done' AND score >= 7 ORDER BY timestamp ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # 3. Filter and Group
    albums_data = filter_and_group_images(rows)
    
    # 4. Process Images and Render Album Pages
    env = Environment(loader=FileSystemLoader(templates_dir))
    album_template = env.get_template("album.html")
    index_template = env.get_template("index.html")
    
    albums_summary = []
    
    for name, photos in albums_data.items():
        slug = name.lower().replace(" ", "_")
        album_dir = os.path.join(out_dir, "assets", slug)
        album_html_path = os.path.join(out_dir, "albums", f"{slug}.html")

        # Check if this album needs rebuilding:
        # An album is stale if its HTML doesn't exist, or any source photo is
        # newer than the existing HTML file.
        album_html_mtime = os.path.getmtime(album_html_path) if os.path.exists(album_html_path) else 0
        album_is_stale = not os.path.exists(album_html_path) or any(
            os.path.getmtime(p["path"]) > album_html_mtime
            for p in photos
            if os.path.exists(p["path"])
        )

        # Always process images incrementally (skips already-done ones)
        processed_photos = []
        for photo in photos:
            filename = os.path.basename(photo["path"])
            thumb, full = process_image(photo["path"], album_dir, slug, filename)
            processed_photos.append({
                "thumb": thumb,
                "full_res": full,
                "description": photo["description"],
                "rating": photo["rating"],
                "score": photo["score"]
            })
            
        # Determine Cover Photo
        album_src_path = os.path.dirname(photos[0]["path"])
        raw_cover_path = get_cover_photo(album_src_path, photos)
        
        # Process cover thumbnail (skipped if already exists)
        cover_filename = "album_cover_" + os.path.basename(raw_cover_path)
        cover_thumb, _ = process_image(raw_cover_path, album_dir, slug, cover_filename)
        
        # Only re-render HTML if album is stale
        if album_is_stale:
            album_html = album_template.render(
                album_name=name,
                photos=processed_photos,
                root_path="../"
            )
            with open(album_html_path, "w", encoding="utf-8") as f:
                f.write(album_html)
            print(f"  [rebuilt] {name}")
        else:
            print(f"  [skipped] {name} (no changes)")
            
        albums_summary.append({
            "name": name,
            "slug": slug,
            "photo_count": len(processed_photos),
            "cover_thumb": cover_thumb
        })
        
    # 5. Render Index Page
    index_html = index_template.render(
        albums=albums_summary,
        root_path=""
    )
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
        
    print(f"Site generated successfully in {out_dir}/")

if __name__ == "__main__":
    generate_site()
