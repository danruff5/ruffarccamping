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

