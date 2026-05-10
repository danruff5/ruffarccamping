# Static Site Generator Design

## 1. Overview
The goal is to generate a static website (hosted on GitHub Pages) to showcase the best photos from the local SQLite database (`data.db`). Photos are selected based on their rating/score, and duplicate photos are excluded based on description similarity.

## 2. Data Processing & Filtering
- **Tool:** A standalone Python script (`build_site.py`).
- **Data Source:** Connects to `data.db` and queries the `images` table.
- **Filtering Logic:**
  - Includes images where `status='Done'` and `score` meets a minimum threshold (e.g., `>= 7`, configurable).
  - Groups images into albums based on the parent folder name of their `path` (each folder represents a camping trip).
  - Within each album, sorts the images by `timestamp` ascending.
  - **Deduplication:** Uses Python's `difflib.SequenceMatcher` to compare the `description` of the current image with the previously accepted image in the album. If the similarity is >85%, the current image is excluded.
- **Image Processing:** Uses `Pillow` to generate optimized WebP thumbnails (e.g., max width 800px) and copies the original full-resolution images.

## 3. Architecture & Output Directory
- **Separation of Concerns:** To avoid conflicts with the local AI FastAPI application (which uses the `frontend/` folder), the static site will be generated entirely into a `docs/` folder.
- **Templates:** Jinja2 templates for the static site will be stored in a new `templates/` directory (e.g., `templates/index.html`, `templates/album.html`).
- **Hosting:** GitHub Pages can be natively configured to serve the static site directly from the `/docs` directory on the `main` branch.

## 4. Frontend & UI Design
- **Aesthetics:** Clean, modern, responsive dark-mode layout utilizing CSS grid.
- **Index Page (`docs/index.html`):** Displays a grid of album cards. Each card shows the album name (folder name), a cover photo (the script will prioritize an image named `cover.jpg`, `cover.png`, or `cover.webp` in the album's folder; if none exists, it falls back to the first approved image), and the total number of photos.
- **Album Page (`docs/albums/<album_name>.html`):** 
  - Displays a grid layout of all approved WebP thumbnails for that album, ordered by timestamp.
  - **Interactive Modal:** Clicking any thumbnail opens a full-screen Lightbox overlay. The overlay displays the full-resolution image and its metadata (AI-generated Description, Rating, and Score).
