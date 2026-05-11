import time
import base64
import io
from PIL import Image
from backend.db import get_db_connection
from backend.ai import generate_description_and_rating

MAX_DIMENSION = 768

def encode_image(image_path):
    t0 = time.time()

    img = Image.open(image_path)
    original_size = img.size

    if max(img.size) > MAX_DIMENSION:
        # Use BICUBIC instead of LANCZOS. It's much faster and visually indistinguishable 
        # for AI ingestion purposes (the AI resizes it down to ~336px internally anyway).
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.BICUBIC)

    buffer = io.BytesIO()
    # Optimize: convert to RGB only if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buffer, format="JPEG", quality=85)
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')

    elapsed = time.time() - t0
    kb_size = len(buffer.getvalue()) / 1024
    print(f"    [encode] {original_size[0]}x{original_size[1]} -> {img.size[0]}x{img.size[1]}, "
          f"{kb_size:.0f}KB, took {elapsed:.2f}s")

    return encoded

def process_single_image(img_id, path):
    print(f"\n[*] Processing: {path}")

    try:
        t_total = time.time()
        conn = get_db_connection()
        cursor = conn.cursor()

        base64_img = encode_image(path)

        t_ai = time.time()
        result = generate_description_and_rating(base64_img)
        ai_elapsed = time.time() - t_ai
        total_elapsed = time.time() - t_total

        photo_desc = result["photo_description"]
        summary = result["summary"]
        critique = result["critique"]
        score = result["score"]
        raw = result["raw"]

        # Store: rating = summary headline + full pillar critique body
        full_critique = f"SUMMARY: {summary}\n\n{critique}" if critique else f"SUMMARY: {summary}"

        cursor.execute(
            "UPDATE images SET status='Done', description=?, rating=?, score=?, timestamp=CURRENT_TIMESTAMP, raw_response=? WHERE id=?",
            (photo_desc, full_critique, score, raw, img_id)
        )

        score_str = f"{score}/10" if score is not None else "N/A"
        print(f"    [ai]     inference took {ai_elapsed:.2f}s | score={score_str}")
        # Print raw tail so we can verify tag parsing
        raw_tail = raw[-400:].replace('\n', ' | ')
        print(f"    [raw]    ...{raw_tail}")
        print(f"    [desc]   '{photo_desc[:80]}{'...' if len(photo_desc) > 80 else ''}'")
        print(f"    [summ]   '{summary[:80]}{'...' if len(summary) > 80 else ''}'")
        print(f"    [total]  {total_elapsed:.2f}s")
        print(f"[+] Done: {path}")

        conn.commit()
    except Exception as e:
        print(f"[!] Failed: {path} - Error: {str(e)}")
        # Try a fresh connection for error logging if the main one failed
        try:
            err_conn = get_db_connection()
            err_conn.execute(
                "UPDATE images SET status='Failed', description=? WHERE id=?",
                (f"Error: {str(e)}", img_id)
            )
            err_conn.commit()
            err_conn.close()
        except:
            pass
    finally:
        try:
            conn.close()
        except:
            pass

    return True
