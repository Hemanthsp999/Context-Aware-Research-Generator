import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_home():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Research Assistant API" in resp.json()["message"]


def test_research_and_history_flow():
    response = client.post("/research", json={
        "topic": "Is egg veg or non-veg",
        "follow_up": False,
        "conversation_id": "test_conv"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Is egg veg or non-veg"
    assert "summary" in data
    assert "references" in data

    hist_resp = client.get("/research/history/test_conv")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["brief_count"] >= 1
    assert any(b["topic"] == "Is egg veg or non-veg" for b in hist_data["briefs"])

