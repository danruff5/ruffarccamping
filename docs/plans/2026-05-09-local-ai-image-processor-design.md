# Local AI Image Processor Design

## Purpose
A self-hosted web application that leverages local CUDA-accelerated Vision Language Models to process large batches of images, generating subjective ratings and descriptions stored in a SQLite database.

## Architecture & Components
* **AI Engine:** **Ollama** running locally. We will default to a lightweight but capable vision model (like `llava` or `moondream`) that comfortably fits in the RTX 5050's VRAM and processes images rapidly.
* **Backend Server:** **Python + FastAPI**. It will host the web interface, manage a background queue, and talk to Ollama.
* **Database:** **SQLite**. We'll create a simple table to store: Image Path, Status (Pending, Processing, Done), Description, and Rating.
* **Frontend UI:** A modern Web Dashboard built with plain HTML, JS, and TailwindCSS (served directly by FastAPI).

## Data Flow & User Experience
1. **Access:** You open the dashboard on your laptop (or any phone/PC on your home Wi-Fi via your laptop's IP).
2. **Setup:** In the UI, you define the target folder containing your images and set your "Prompt/Rubric" (e.g., *"Describe the subject and rate the composition from 1-10"*).
3. **Queueing:** The backend scans the folder and populates the SQLite database with all the pending images.
4. **Processing:** A background worker sequentially grabs images, sends them to Ollama via API, and updates the database with the results.
5. **Real-time Monitoring:** The web dashboard updates automatically, showing a progress bar and a live feed of the processed images alongside their new AI-generated descriptions and ratings.
