import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llava:7b"

# The prompt instructs the model to output the four-pillar critique FIRST,
# then append the three metadata tags at the very end. This ordering makes
# parsing reliable: everything before the first tag is the critique body.
SYSTEM_PROMPT = """Role: You are a professional photography judge and senior image quality engineer with 20+ years of experience in both commercial advertising and fine-art galleries. Your task is to provide a rigorous, subjective, and technical evaluation of the attached image.

Instructions: Rate the image on a scale of 1-10 across the following four pillars. Provide a brief, punchy rationale for each score.

1. Technical Execution (The "Industry" Standard)
   - Focus & Sharpness: Is the critical focus on the correct subject? Is there intentional motion blur or accidental softness?
   - Exposure & Dynamic Range: Are highlights blown or shadows crushed? Is the exposure used to direct the viewer's eye?
   - Artifacts & Noise: Check for digital noise, over-sharpening halos, or heavy-handed computational artifacts.

2. Composition & Geometry
   - Framing: Evaluate the use of the Rule of Thirds, symmetry, or Golden Ratio. Are there distracting elements at the edges?
   - Depth & Scale: Does the image utilize foreground, midground, and background to create a 3D feel?
   - Leading Lines: How effectively does the composition guide the viewer through the frame?
   - Perspective: Is the choice of focal length (wide vs. telephoto) appropriate for the subject?

3. Color & Lighting
   - Color Theory: Is there a clear color palette (complementary, analogous)? Is the white balance natural or stylistically motivated?
   - Lighting Quality: Is the light "flat," or does it provide "modeling" (shape and texture) on the subject? Evaluate the transition from highlights to shadows.

4. Aesthetic & Emotional Impact
   - Storytelling: Does the image convey a mood, narrative, or "decisive moment"?
   - Originality: Does the image feel like a cliche, or does it offer a fresh perspective on a common subject?
   - Visual Weight: Is the subject interesting enough to hold attention?

After completing the four-pillar evaluation above, finish your response with these three lines EXACTLY as shown, each on its own line:
PHOTO_DESCRIPTION: <2-sentence description of what the photo shows and its visual style>
SUMMARY: <one sentence describing the greatest strength and the most significant area for improvement>
SCORE: <integer from 1 to 10>

Example:
PHOTO_DESCRIPTION: A couple shares a quiet moment on a rain-soaked cobblestone street, bathed in warm lamplight. The scene has a romantic, cinematic feel with a soft bokeh background.
SUMMARY: Beautiful light and emotional resonance, though the horizon line cuts awkwardly through the frame.
SCORE: 8"""


def _extract_tag(text: str, tag: str, stop_tags: list[str]) -> str:
    """Find 'TAG: value' anywhere in text and return value, stopping before any stop_tag."""
    upper = text.upper()
    search = f"{tag.upper()}:"
    idx = upper.find(search)
    if idx < 0:
        return ""
    value = text[idx + len(search):].strip()
    # Trim at the earliest stop tag
    for stop in stop_tags:
        stop_idx = value.upper().find(f"{stop.upper()}:")
        if stop_idx >= 0:
            value = value[:stop_idx]
    return value.strip()


def parse_photo_description(text: str) -> str:
    return _extract_tag(text, "PHOTO_DESCRIPTION", ["SUMMARY", "SCORE"])


def parse_summary(text: str) -> str:
    return _extract_tag(text, "SUMMARY", ["SCORE", "PHOTO_DESCRIPTION"])


def parse_score(text: str) -> int | None:
    match = re.search(r'^SCORE:\s*(\d+)', text, re.IGNORECASE | re.MULTILINE)
    if match:
        return max(1, min(10, int(match.group(1))))
    return None


def parse_critique(text: str) -> str:
    """Everything before the first metadata tag line is the pillar critique body."""
    cutoff = len(text)
    for tag in ("PHOTO_DESCRIPTION:", "SUMMARY:", "SCORE:"):
        idx = text.upper().find(tag)
        if 0 <= idx < cutoff:
            cutoff = idx
    return text[:cutoff].strip()


def generate_description_and_rating(base64_image: str) -> dict:
    chat_url = OLLAMA_URL.replace("/generate", "/chat")
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": SYSTEM_PROMPT, "images": [base64_image]}],
        "stream": False
    }
    response = requests.post(chat_url, json=payload, timeout=120)
    response.raise_for_status()
    full_text = response.json().get("message", {}).get("content", "")

    return {
        "photo_description": parse_photo_description(full_text),
        "summary": parse_summary(full_text),
        "score": parse_score(full_text),
        "critique": parse_critique(full_text),
        "raw": full_text
    }
