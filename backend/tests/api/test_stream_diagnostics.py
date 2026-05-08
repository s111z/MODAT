"""流式传输诊断接口测试。"""

import json


class TestMinimalStreamEndpoint:

    def test_test_stream_returns_sse_headers(self, test_client):
        resp = test_client.get("/api/test-stream?count=2&interval=0")

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert resp.headers["cache-control"] == "no-cache"
        assert resp.headers["x-accel-buffering"] == "no"

    def test_test_stream_emits_chunks_and_done_event(self, test_client):
        resp = test_client.get("/api/test-stream?count=3&interval=0")
        lines = [line for line in resp.text.strip().split("\n") if line.startswith("data: ")]
        events = [json.loads(line.removeprefix("data: ")) for line in lines]

        assert [event["type"] for event in events] == [
            "test_stream",
            "test_stream",
            "test_stream",
            "test_stream_done",
        ]
        assert [event.get("index") for event in events[:-1]] == [1, 2, 3]
        assert all("timestamp" in event for event in events)
