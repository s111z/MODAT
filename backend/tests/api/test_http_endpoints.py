"""HTTP API 端点完整测试"""

import pytest
import json
import io
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestRootEndpoints:

    def test_root(self, test_client):
        resp = test_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == "2.0.0"
        assert data["status"] == "running"
        assert "智能文档评审" in data["message"]

    def test_health(self, test_client):
        resp = test_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


# ===== Chat API =====

@pytest.mark.integration
class TestChatEndpoint:

    @patch("main.create_qa_workflow")
    def test_chat_success(self, mock_wf, test_client):
        mock_result = {
            "response": "测试回复",
            "steps": ["步骤1", "步骤2"],
            "intent": "knowledge_qa",
        }
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = mock_result
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat", json={"message": "测试问题"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "测试回复"
        assert len(data["steps"]) == 2
        assert "session_id" in data

    @patch("main.create_qa_workflow")
    def test_chat_with_session_id(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {"response": "ok", "steps": []}
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat", json={
            "message": "测试",
            "session_id": "my-session-123",
        })
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "my-session-123"

    @patch("main.create_qa_workflow")
    def test_chat_auto_generates_session_id(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {"response": "ok", "steps": []}
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat", json={"message": "测试"})
        sid = resp.json()["session_id"]
        assert sid is not None
        assert len(sid) > 0

    @patch("main.create_qa_workflow")
    def test_chat_workflow_exception(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.side_effect = Exception("workflow crashed")
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat", json={"message": "测试"})
        assert resp.status_code == 500
        assert "workflow crashed" in resp.json()["detail"]


# ===== Chat Stream API =====

@pytest.mark.integration
class TestChatStreamEndpoint:

    @patch("main.create_qa_workflow")
    def test_stream_returns_sse(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {"response": "流式回复", "steps": ["s1", "s2"]}
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat/stream", json={"message": "测试"})
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

    @patch("main.create_qa_workflow")
    def test_stream_contains_data_lines(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {"response": "答案", "steps": ["步骤A"]}
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat/stream", json={"message": "测试"})
        body = resp.text

        # SSE格式: 每行以 "data: " 开头
        lines = [l for l in body.strip().split("\n") if l.startswith("data: ")]
        assert len(lines) >= 2  # 至少有meta和response

        # 解析最后一行(response)
        last_data = json.loads(lines[-1].removeprefix("data: "))
        assert last_data["type"] == "response"
        assert last_data["content"] == "答案"

    @patch("main.create_qa_workflow")
    def test_stream_contains_session_id(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {"response": "ok", "steps": []}
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/chat/stream", json={
            "message": "测试",
            "session_id": "stream-session-1",
        })
        body = resp.text
        lines = [l for l in body.strip().split("\n") if l.startswith("data: ")]

        # 第一条应该是meta
        meta = json.loads(lines[0].removeprefix("data: "))
        assert meta["type"] == "meta"
        assert meta["session_id"] == "stream-session-1"


# ===== Review API =====

@pytest.mark.integration
class TestReviewEndpoint:

    @patch("main.create_review_workflow")
    def test_review_file_not_found(self, mock_wf, test_client):
        resp = test_client.post("/api/review", json={
            "filename": "nonexistent_file.pdf",
            "message": "审核测试",
        })
        assert resp.status_code == 404
        assert "文件不存在" in resp.json()["detail"]

    @patch("main.create_review_workflow")
    @patch("os.path.exists", return_value=True)
    def test_review_success(self, mock_exists, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {
            "response": "审核报告内容",
            "steps": ["解析", "抽取", "检索", "生成"],
        }
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/review", json={
            "filename": "test.pdf",
            "message": "请审核此方案",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "审核报告内容"
        assert len(data["steps"]) == 4
        assert "session_id" in data


# ===== Upload API =====

@pytest.mark.unit
class TestUploadEndpoints:

    def test_upload_pdf(self, test_client):
        resp = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["savefilename"].endswith(".pdf")
        assert "test" in data["savefilename"]

    def test_upload_docx(self, test_client):
        resp = test_client.post(
            "/api/upload",
            files={"file": ("doc.docx", io.BytesIO(b"PK\x03\x04 fake"), "application/octet-stream")},
        )
        assert resp.status_code == 200
        assert resp.json()["savefilename"].endswith(".docx")

    def test_upload_txt(self, test_client):
        resp = test_client.post(
            "/api/upload",
            files={"file": ("readme.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 200
        assert resp.json()["savefilename"].endswith(".txt")

    def test_upload_exe_rejected(self, test_client):
        resp = test_client.post(
            "/api/upload",
            files={"file": ("virus.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_xlsx_rejected(self, test_client):
        resp = test_client.post(
            "/api/upload",
            files={"file": ("data.xlsx", io.BytesIO(b"PK"), "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_knowledge_upload_pdf(self, test_client):
        resp = test_client.post(
            "/api/knowledge_upload",
            files={"file": ("knowledge.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_knowledge_upload_rejected(self, test_client):
        resp = test_client.post(
            "/api/knowledge_upload",
            files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
        )
        assert resp.status_code == 400

    def test_upload_returns_size(self, test_client):
        content = b"x" * 1024
        resp = test_client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(content), "application/pdf")},
        )
        assert resp.json()["size"] == 1024


# ===== Task API =====

@pytest.mark.integration
class TestTaskEndpoints:

    def test_get_task_not_found(self, test_client):
        resp = test_client.get("/api/task/nonexistent-id")
        assert resp.status_code == 404
        assert "任务不存在" in resp.json()["detail"]

    def test_list_tasks_empty(self, test_client):
        resp = test_client.get("/api/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_list_tasks_with_session_filter(self, test_client):
        resp = test_client.get("/api/tasks?session_id=nonexistent")
        assert resp.status_code == 200
        assert resp.json()["tasks"] == []

    @patch("os.path.exists", return_value=True)
    def test_submit_task(self, mock_exists, test_client):
        resp = test_client.post("/api/task/submit", json={
            "filename": "test.pdf",
            "message": "审核",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["message"] == "任务已提交"

        # 提交后能查询到
        task_id = data["task_id"]
        resp2 = test_client.get(f"/api/task/{task_id}")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "pending"

    def test_submit_task_file_not_found(self, test_client):
        resp = test_client.post("/api/task/submit", json={
            "filename": "not_exist.pdf",
            "message": "审核",
        })
        assert resp.status_code == 404


# ===== VectorDB API =====

@pytest.mark.integration
class TestVectorDBEndpoints:

    @patch("main.create_vectordb_workflow")
    def test_vectordb_search(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {
            "success": True,
            "message": "找到2条",
            "results": [{"content": "test"}],
            "steps": ["搜索"],
        }
        mock_wf.return_value = mock_compiled

        resp = test_client.post("/api/vectordb/search", json={"query": "测试"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("main.create_vectordb_workflow")
    def test_vectordb_list(self, mock_wf, test_client):
        mock_compiled = MagicMock()
        mock_compiled.invoke.return_value = {
            "success": True,
            "message": "ok",
            "results": [],
            "steps": [],
        }
        mock_wf.return_value = mock_compiled

        resp = test_client.get("/api/vectordb/list")
        assert resp.status_code == 200

    def test_vectordb_delete_no_params(self, test_client):
        resp = test_client.post("/api/vectordb/delete", json={})
        assert resp.status_code == 400
        assert "必须提供" in resp.json()["detail"]
