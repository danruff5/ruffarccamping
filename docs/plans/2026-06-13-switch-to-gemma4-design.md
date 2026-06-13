# Switch to Gemma 4 12B Vision Model

This design document outlines switching the local AI image evaluation model from `llava:7b` to `gemma4:12b` for the photo critique application.

## User Review Required

No major breaking changes are expected, but the `gemma4:12b` model must be pulled locally.

## Proposed Changes

### Backend AI Configuration

#### [MODIFY] [ai.py](file:///c:/Users/dckra/Desktop/ruffarc/backend/ai.py)
* Update `MODEL_NAME = "gemma4:12b"`.

## Verification Plan

### Manual Verification
1. Start the Ollama server and run `ollama pull gemma4:12b`.
2. Launch the backend server using `start.ps1`.
3. Check the `/api/health` endpoint to confirm the model status is `Ready`.
4. Test photo upload and processing to verify that the structured output tags are parsed correctly.
