# Switch to Qwen 2.5 VL Implementation Plan

> **For Antigravity:** REQUIRED SUB-SKILL: Load executing-plans to implement this plan task-by-task.

**Goal:** Switch the photo app's image classification model from `gemma4:12b` to `qwen2.5-vl`.

**Architecture:** Update the `MODEL_NAME` constant in `backend/ai.py` to target `qwen2.5-vl`. Verify that Ollama pulls the new model, and parses the structured responses correctly.

**Tech Stack:** Python 3.14+, Ollama (local server), pytest, requests, FastAPI.

---

### Task 1: Pull the Qwen 2.5 VL Model

**Files:**
- Modify: None (operational task)

**Step 1: Pull model via Ollama**

Run: `ollama pull qwen2.5-vl`
Expected: Download completes successfully.

**Step 2: Verify model availability**

Run: `python -c "import requests; print(any('qwen2.5-vl' in m['name'] for m in requests.get('http://127.0.0.1:11434/api/tags').json().get('models', [])))"`
Expected: Prints `True`

**Step 3: Commit**

Since this is an environment setup step, no git commit is needed for this task.

---

### Task 2: Update Model Name and Fix Unit Mock Test

**Files:**
- Modify: `backend/ai.py:5`
- Modify: `tests/test_ai.py`

**Step 1: Write the failing test**

We need to fix the calls inside `tests/test_ai.py` to assert the updated model name.

Modify `tests/test_ai.py` to expect `qwen2.5-vl` model request:
```python
    def mock_post(url, json, timeout):
        # Assert that the new model name is requested
        assert json["model"] == "qwen2.5-vl"
        return MockResponse()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ai.py`
Expected: FAIL due to `AssertionError` (model requested is still `gemma4:12b`).

**Step 3: Write minimal implementation**

Modify `backend/ai.py` to change the model name:
```python
MODEL_NAME = "qwen2.5-vl"
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ai.py`
Expected: PASS

**Step 5: Commit**

Run:
```bash
git add backend/ai.py tests/test_ai.py ; git commit -m "feat: switch model to qwen2.5-vl and fix mock tests"
```

---

### Task 3: Run Ollama Integration Tests

**Files:**
- Modify: None

**Step 1: Run integration test suite**

Run: `python -m pytest tests/test_ollama_integration.py`
Expected: PASS
