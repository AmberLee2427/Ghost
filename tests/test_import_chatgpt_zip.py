import pytest
import json
import zipfile
import tempfile
import os
import shutil
from fastapi.testclient import TestClient
from ghost_brain.server import create_app, get_brain
from ghost_brain.brain import Brain


class TestChatGPTZipImport:
    """Test ChatGPT ZIP import functionality with attachments."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        # Dependency override: inject a fresh Brain for each test
        def test_brain():
            brain = Brain()
            import asyncio
            asyncio.get_event_loop().run_until_complete(brain.initialize())
            return brain
        app.dependency_overrides[get_brain] = test_brain
        return TestClient(app)
    
    def create_test_zip_with_attachments(self):
        temp_dir = tempfile.mkdtemp()
        conversations = [
            {
                "id": "conv1",
                "title": "Test Conversation",
                "mapping": {
                    "msg1": {
                        "id": "msg1",
                        "message": {
                            "id": "msg1",
                            "author": {"role": "user"},
                            "content": {
                                "content_type": "text",
                                "parts": ["Hello, can you help me with this file?"],
                                "attachments": [
                                    {
                                        "name": "test.txt",
                                        "type": "text/plain",
                                        "path": "attachments/test.txt"
                                    },
                                    {
                                        "name": "data.json",
                                        "type": "application/json", 
                                        "path": "attachments/data.json"
                                    }
                                ]
                            },
                            "create_time": 1234567890
                        }
                    },
                    "msg2": {
                        "id": "msg2", 
                        "message": {
                            "id": "msg2",
                            "author": {"role": "assistant"},
                            "content": {
                                "content_type": "text",
                                "parts": ["I can help you with that file!"]
                            },
                            "create_time": 1234567891
                        }
                    }
                }
            }
        ]
        conv_path = os.path.join(temp_dir, "conversations.json")
        with open(conv_path, "w") as f:
            json.dump(conversations, f)
        attachments_dir = os.path.join(temp_dir, "attachments")
        os.makedirs(attachments_dir)
        txt_path = os.path.join(attachments_dir, "test.txt")
        with open(txt_path, "w") as f:
            f.write("This is a test text file with some content.")
        json_path = os.path.join(attachments_dir, "data.json")
        with open(json_path, "w") as f:
            json.dump({"key": "value", "number": 42}, f)
        zip_path = os.path.join(temp_dir, "test_export.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(conv_path, "conversations.json")
            zipf.write(txt_path, "attachments/test.txt")
            zipf.write(json_path, "attachments/data.json")
        return zip_path, temp_dir
    
    def test_import_zip_with_attachments(self, client):
        zip_path, temp_dir = self.create_test_zip_with_attachments()
        try:
            with client:
                with open(zip_path, "rb") as f:
                    response = client.post(
                        "/chat-history/import-zip",
                        files={"file": ("test_export.zip", f, "application/zip")},
                        data={"user_id": "test_user"}
                    )
                assert response.status_code == 200
                result = response.json()
                assert result["status"] == "success"
                assert result["files_processed"] == 1
                assert result["chunks_embedded"] == 2
                assert result["attachments_processed"] == 2
                assert result["chunks_skipped"] == 0
                assert len(result["errors"]) == 0
        finally:
            shutil.rmtree(temp_dir)
    
    def test_attachment_metadata_storage(self, client):
        pass
    
    def test_text_attachment_embedding(self, client):
        pass
    
    def test_attachment_stats_endpoint(self, client):
        zip_path, temp_dir = self.create_test_zip_with_attachments()
        try:
            with client:
                with open(zip_path, "rb") as f:
                    client.post(
                        "/chat-history/import-zip",
                        files={"file": ("test_export.zip", f, "application/zip")},
                        data={"user_id": "test_user"}
                    )
                response = client.get("/attachments/stats")
                assert response.status_code == 200
                stats = response.json()
                assert stats["total_attachments"] == 2
                assert stats["embedded_attachments"] == 2
                assert "text/plain" in stats["type_counts"]
                assert "application/json" in stats["type_counts"]
        finally:
            shutil.rmtree(temp_dir)
    
    def test_get_message_attachments(self, client):
        zip_path, temp_dir = self.create_test_zip_with_attachments()
        try:
            with client:
                with open(zip_path, "rb") as f:
                    client.post(
                        "/chat-history/import-zip",
                        files={"file": ("test_export.zip", f, "application/zip")},
                        data={"user_id": "test_user"}
                    )
                response = client.get("/attachments/message/chat_msg1")
                assert response.status_code == 200
                attachments = response.json()
                assert len(attachments) == 2
                txt_attachment = next(a for a in attachments if a["filename"] == "test.txt")
                assert txt_attachment["file_type"] == "text/plain"
                assert txt_attachment["embedded"] == True
                assert "This is a test text file" in txt_attachment["content_text"]
                json_attachment = next(a for a in attachments if a["filename"] == "data.json")
                assert json_attachment["file_type"] == "application/json"
                assert json_attachment["embedded"] == True
                assert "key" in json_attachment["content_text"]
        finally:
            shutil.rmtree(temp_dir) 