import requests
import base64
import pytest
from backend.ai import OLLAMA_URL, MODEL_NAME

def test_ollama_connection():
    """Check if the Ollama server is running and reachable."""
    try:
        # Ollama usually has a root endpoint or /api/tags
        base_url = OLLAMA_URL.replace("/generate", "/tags")
        response = requests.get(base_url, timeout=5)
        assert response.status_code == 200, f"Ollama server returned {response.status_code}"
    except requests.exceptions.ConnectionError:
        pytest.fail("Ollama server is not running at localhost:11434. Please start Ollama.")

def test_model_availability():
    """Check if the configured model is pulled and available."""
    base_url = OLLAMA_URL.replace("/generate", "/tags")
    response = requests.get(base_url)
    models = response.json().get("models", [])
    model_names = [m["name"] for m in models]
    
    # Check for exact match or versioned match (e.g., llava:7b)
    assert any(MODEL_NAME in name for name in model_names), \
        f"Model '{MODEL_NAME}' not found in Ollama. Run 'ollama pull {MODEL_NAME}'"

def test_text_processing():
    """Test if the model can handle basic text generation without images."""
    payload = {
        "model": MODEL_NAME,
        "prompt": "Say hello!",
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code != 200:
            pytest.fail(f"Ollama text generation failed: {response.text}")
        assert len(response.json().get("response", "")) > 0
    except Exception as e:
        pytest.fail(f"Text processing failed: {str(e)}")

import os
import glob

def test_vision_processing():
    """Test if the model can process a REAL image from the user's folder."""
    # Find the first image in the user's folder
    photo_dir = r"C:\Users\dckra\Desktop\Good Photos"
    image_files = []
    for ext in ['*.jpg', '*.png', '*.jpeg']:
        image_files.extend(glob.glob(os.path.join(photo_dir, ext)))
    
    if not image_files:
        pytest.skip(f"No images found in {photo_dir} to test with.")
        
    test_image_path = image_files[0]
    
    # Encode real image
    with open(test_image_path, "rb") as f:
        real_image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    chat_url = OLLAMA_URL.replace("/generate", "/chat")
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": "Describe this photo briefly.",
                "images": [real_image_base64]
            }
        ],
        "stream": False
    }
    
    try:
        print(f"\n[*] Testing with real image: {test_image_path}")
        response = requests.post(chat_url, json=payload, timeout=120)
        if response.status_code != 200:
            pytest.fail(f"Ollama vision chat failed ({response.status_code}): {response.text}")
        
        result = response.json().get("message", {}).get("content", "").lower()
        assert len(result) > 0, "Model returned empty response"
        print(f"Vision response: {result}")
    except Exception as e:
        pytest.fail(f"Vision chat failed: {str(e)}")
