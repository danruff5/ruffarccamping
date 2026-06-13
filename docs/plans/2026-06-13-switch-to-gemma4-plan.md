# Switch to Gemma 4 12B Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Switch the photo app's image classification model from `llava:7b` to `gemma4:12b`.

**Architecture:** Update the `MODEL_NAME` constant in `backend/ai.py` to target `gemma4:12b`. Verify that the Ollama service starts correctly, pulls the new model, and parses the structured responses correctly.

**Tech Stack:** Python 3.14+, Ollama (local server), pytest, requests, FastAPI.

---

### Task 1: Pull the Gemma 4 12B Model

**Files:**
- Modify: None (operational task)

**Step 1: Pull model via Ollama**

Run: `ollama pull gemma4:12b`
Expected: Download completes successfully.

**Step 2: Verify model availability**

Run: `python -c "import requests; print(any('gemma4:12b' in m['name'] for m in requests.get('http://127.0.0.1:11434/api/tags').json().get('models', [])))"`
Expected: Prints `True`

**Step 3: Commit**

Since this is an environment setup step, no git commit is needed for this task.

---

### Task 2: Update Model Name and Fix Unit Mock Test

**Files:**
- Modify: `backend/ai.py:5`
- Modify: `tests/test_ai.py`

**Step 1: Write the failing test**

We need to fix the call inside `tests/test_ai.py` where `generate_description_and_rating` was called with two arguments (outdated signature) and assert the updated model name.

Modify `tests/test_ai.py` to:
```python
from backend.ai import generate_description_and_rating, MODEL_NAME
import pytest

def test_generate_description_mock(monkeypatch):
    class MockResponse:
        def json(self):
            return {
                "message": {
                    "content": "Critique body\nPHOTO_DESCRIPTION: A nice dog.\nSUMMARY: A good boy.\nSCORE: 8"
                }
            }
        def raise_for_status(self):
            pass
    
    def mock_post(url, json, timeout):
        # Assert that the new model name is requested
        assert json["model"] == "gemma4:12b"
        return MockResponse()
        
    monkeypatch.setattr("requests.post", mock_post)
    
    result = generate_description_and_rating("mock_base64_image")
    assert result["photo_description"] == "A nice dog."
    assert result["summary"] == "A good boy."
    assert result["score"] == 8
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ai.py`
Expected: FAIL due to `AssertionError` (model requested is still `llava:7b`) or `TypeError` (if signature mismatch not resolved).

**Step 3: Write minimal implementation**

Modify `backend/ai.py` to change the model name:
```python
MODEL_NAME = "gemma4:12b"
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ai.py`
Expected: PASS

**Step 5: Commit**

Run:
```bash
git add backend/ai.py tests/test_ai.py ; git commit -m "feat: switch model to gemma4:12b and fix ai mock tests"
```

---

### Task 3: Run Ollama Integration Tests

**Files:**
- Modify: None

**Step 1: Run integration test suite**

Run: `python -m pytest tests/test_ollama_integration.py`
Expected: PASS (if Ollama is running and has the model pulled).
