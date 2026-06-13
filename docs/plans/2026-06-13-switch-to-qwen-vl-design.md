# Switch to Qwen 2.5 VL 7B Vision Model

This design document outlines switching the local AI image evaluation model from `gemma4:12b` to `qwen2.5-vl` to optimize performance and prevent VRAM-split timeouts.

## Proposed Changes

### Backend AI Configuration

#### [MODIFY] [ai.py](file:///c:/Users/dckra/Desktop/ruffarc/backend/ai.py)
* Update `MODEL_NAME = "qwen2.5-vl"`.

### Unit Tests

#### [MODIFY] [test_ai.py](file:///c:/Users/dckra/Desktop/ruffarc/tests/test_ai.py)
* Update unit test mocks to expect `"qwen2.5-vl"` as the model parameter.

## Verification Plan

### Manual Verification
1. Run `ollama pull qwen2.5-vl`.
2. Run unit tests (`python -m pytest tests/test_ai.py`) and integration tests (`python -m pytest tests/test_ollama_integration.py`).
