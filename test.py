import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_submit_reaction_time():
    payload = {
        "patient_id": "test-123",
        "age_group": "50-64",
        "reaction_times_ms": [250, 260, 255, 245, 270, 260, 250, 240, 255, 265]
    }
    response = client.post("/api/v1/reaction-time/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "test-123"
    assert data["median_ms"] == 255.0
    assert "severity" in data["median_classification"]

def test_submit_reaction_time_invalid_length():
    payload = {
        "patient_id": "test-123",
        "age_group": "50-64",
        "reaction_times_ms": [250, 260, 255]  # Only 3 values, 10 required
    }
    response = client.post("/api/v1/reaction-time/submit", json=payload)
    assert response.status_code == 422

def test_get_trial_timing():
    response = client.get("/api/v1/reaction-time/trial-timing?trial_number=5")
    assert response.status_code == 200
    data = response.json()
    assert data["trial_number"] == 5
    assert 2000 <= data["delay_ms"] <= 6000

def test_submit_digit_span():
    payload = {
        "patient_id": "test-456",
        "forward_span": 6,
        "backward_span": 5
    }
    response = client.post("/api/v1/digit-span/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["gap"] == 1
    assert data["forward_classification"]["severity"] == "normal"
    assert data["summary"] == "✅ Within normal limits"

def test_get_digit_sequence():
    response = client.get("/api/v1/digit-span/sequence?length=5")
    assert response.status_code == 200
    data = response.json()
    assert data["length"] == 5
    assert len(data["sequence"]) == 5

if __name__ == "__main__":
    pytest.main(["-v", "test.py"])
