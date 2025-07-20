import pytest
import tempfile
import zipfile
import json
import os
import requests

@pytest.fixture
def fake_chatgpt_zip():
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmpzip:
        conversations = [
            {
                "id": "conv1",
                "title": "Test Conversation",
                "mapping": {
                    "1": {
                        "id": "1",
                        "message": {
                            "id": "1",
                            "author": {"role": "user"},
                            "create_time": 1234567890,
                            "content": {"parts": ["Hello, assistant!"]}
                        }
                    },
                    "2": {
                        "id": "2",
                        "message": {
                            "id": "2",
                            "author": {"role": "assistant"},
                            "create_time": 1234567891,
                            "content": {"parts": ["Hello, user!"]}
                        }
                    }
                }
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            conv_path = os.path.join(tmpdir, "conversations.json")
            with open(conv_path, "w", encoding="utf-8") as f:
                json.dump(conversations, f)
            with zipfile.ZipFile(tmpzip.name, "w") as zf:
                zf.write(conv_path, arcname="conversations.json")
        yield tmpzip.name
    os.remove(tmpzip.name)

def test_import_chatgpt_zip(fake_chatgpt_zip):
    url = "http://localhost:8000/chat-history/import-zip"
    with open(fake_chatgpt_zip, "rb") as f:
        files = {"file": ("test.zip", f, "application/zip")}
        data = {"user_id": "test_user"}
        resp = requests.post(url, files=files, data=data)
    assert resp.status_code == 200, f"Unexpected status: {resp.status_code}, body: {resp.text}"
    result = resp.json()
    assert result["status"] == "success", f"Unexpected result: {result}"
    assert result["files_processed"] == 1, f"Unexpected files_processed: {result}"
    assert result["chunks_embedded"] == 2, f"Unexpected chunks_embedded: {result}"
    assert result["chunks_skipped"] == 0, f"Unexpected chunks_skipped: {result}"
    assert not result["errors"], f"Errors: {result['errors']}" 