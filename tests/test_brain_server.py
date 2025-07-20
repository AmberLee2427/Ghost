import requests

def test_health():
    resp = requests.get("http://localhost:8000/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["initialized"] is True
    assert data["memory"] == "ok"
    assert data["llm"] in ("ok", "no_keys")


def test_chat():
    payload = {
        "message": "Hello, brain!",
        "history": [],
        "user_id": "pytest_user",
        "system_prompt": None,
        "model_type": None,
        "model_name": None,
        "use_structured_response": False
    }
    resp = requests.post("http://localhost:8000/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "timestamp" in data


def test_memory_stats():
    resp = requests.get("http://localhost:8000/memory/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "message_count" in data
    assert "chunk_count" in data 