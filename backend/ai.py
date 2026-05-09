import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llava:7b" # Or moondream

def generate_description_and_rating(base64_image: str, prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "images": [base64_image],
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json().get("response", "")
