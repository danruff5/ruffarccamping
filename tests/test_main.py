from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

import uuid

def test_add_images():
    unique_path1 = f"img_{uuid.uuid4()}.png"
    unique_path2 = f"img_{uuid.uuid4()}.png"
    response = client.post("/api/images", json={"paths": [unique_path1, unique_path2]})
    assert response.status_code == 200
    assert response.json()["added"] == 2
