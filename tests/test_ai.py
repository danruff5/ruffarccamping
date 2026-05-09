from backend.ai import generate_description_and_rating
import base64

def test_generate_description_mock(monkeypatch):
    # Mock requests.post to avoid needing real Ollama in tests
    class MockResponse:
        def json(self):
            return {"response": "A nice dog. Rating: 8/10"}
        def raise_for_status(self):
            pass
    
    def mock_post(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr("requests.post", mock_post)
    
    result = generate_description_and_rating("mock_base64_image", "Describe this")
    assert "A nice dog" in result
