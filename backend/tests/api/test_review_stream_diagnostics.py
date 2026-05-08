"""方案审核流式传输诊断测试。

这些测试不调用真实 vLLM，也不执行真实审核节点；通过替换 run_review_streaming
验证 /api/review/stream 外层是否能把事件按 SSE 格式输出。
"""

import asyncio
import json
from unittest.mock import patch


async def _fake_run_review_streaming(state, emit, build_workflow_steps, build_review_report, filename):
    await emit({"type": "diagnostic", "stage": "start", "filename": filename})
    await asyncio.sleep(0)
    await emit({"type": "diagnostic", "stage": "middle"})
    await asyncio.sleep(0)
    await emit({
        "type": "final",
        "status": "done",
        "message": "diagnostic complete",
        "reviewData": {"fileName": filename},
    })
    return {
        **state,
        "response": "diagnostic complete",
        "doc_info": {"filename": filename},
        "steps": [],
    }


class TestReviewStreamEndpointDiagnostics:

    @patch("main.os.path.exists", return_value=True)
    @patch("main.run_review_streaming", side_effect=_fake_run_review_streaming)
    def test_review_stream_outer_sse_contract(self, mock_run_streaming, mock_exists, test_client):
        resp = test_client.post("/api/review/stream", json={
            "filename": "diagnostic.txt",
            "message": "诊断流式接口",
            "session_id": "diagnostic-session",
        })

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert resp.headers["cache-control"] == "no-cache"
        assert resp.headers["x-accel-buffering"] == "no"

        lines = [line for line in resp.text.strip().split("\n") if line.startswith("data: ")]
        events = [json.loads(line.removeprefix("data: ")) for line in lines]

        assert [event["type"] for event in events] == [
            "meta",
            "diagnostic",
            "diagnostic",
            "final",
        ]
        assert all(event["session_id"] == "diagnostic-session" for event in events)
        assert [event["seq"] for event in events] == [1, 2, 3, 4]
        assert mock_run_streaming.called

    def test_review_stream_missing_file_returns_404(self, test_client):
        resp = test_client.post("/api/review/stream", json={
            "filename": "missing-file.txt",
            "message": "诊断流式接口",
        })

        assert resp.status_code == 404
        assert "文件不存在" in resp.json()["detail"]
