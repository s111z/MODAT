"""WebSocket连接管理器单元测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from api.websocket_handler import ConnectionManager


@pytest.mark.unit
class TestConnectionManager:

    def setup_method(self):
        self.manager = ConnectionManager()

    def test_connect(self):
        ws = AsyncMock()
        asyncio.get_event_loop().run_until_complete(
            self.manager.connect("s1", ws)
        )
        assert self.manager.is_connected("s1")
        ws.accept.assert_awaited_once()

    def test_disconnect(self):
        ws = AsyncMock()
        asyncio.get_event_loop().run_until_complete(
            self.manager.connect("s1", ws)
        )
        self.manager.disconnect("s1")
        assert not self.manager.is_connected("s1")

    def test_disconnect_nonexistent(self):
        # 不应抛异常
        self.manager.disconnect("not_exist")

    def test_is_connected_false(self):
        assert not self.manager.is_connected("not_exist")

    def test_send_step(self):
        ws = AsyncMock()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.manager.connect("s1", ws))
        loop.run_until_complete(self.manager.send_step("s1", "正在处理..."))
        ws.send_json.assert_awaited_once()
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "step"
        assert call_args["content"] == "正在处理..."

    def test_send_step_not_connected(self):
        # 未连接时不应抛异常
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.manager.send_step("not_exist", "test"))

    def test_send_result(self):
        ws = AsyncMock()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.manager.connect("s1", ws))
        loop.run_until_complete(
            self.manager.send_result("s1", {"response": "回复内容"})
        )
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "result"
        assert call_args["response"] == "回复内容"

    def test_send_error(self):
        ws = AsyncMock()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.manager.connect("s1", ws))
        loop.run_until_complete(self.manager.send_error("s1", "出错了"))
        call_args = ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["content"] == "出错了"

    def test_send_auto_disconnect_on_error(self):
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("connection closed")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.manager.connect("s1", ws))
        loop.run_until_complete(self.manager.send_step("s1", "test"))
        # 发送失败后应自动断开
        assert not self.manager.is_connected("s1")
