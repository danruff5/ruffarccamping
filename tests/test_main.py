from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_add_images():
    response = client.post("/api/images", json={"paths": ["img1.png", "img2.png"]})
    assert response.status_code == 200
    assert response.json()["added"] == 2
