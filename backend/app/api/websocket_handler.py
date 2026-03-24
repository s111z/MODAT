"""
WebSocket连接管理器

支持实时推送Agent工作流执行步骤。
"""

import json
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        """断开连接"""
        self.active_connections.pop(session_id, None)

    async def send_step(self, session_id: str, step: str, agent_name: str = ""):
        """推送Agent执行步骤"""
        ws = self.active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "step",
                    "agent": agent_name,
                    "content": step,
                })
            except Exception:
                self.disconnect(session_id)

    async def send_result(self, session_id: str, result: dict):
        """推送最终结果"""
        ws = self.active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "result",
                    **result,
                })
            except Exception:
                self.disconnect(session_id)

    async def send_error(self, session_id: str, error: str):
        """推送错误信息"""
        ws = self.active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "error",
                    "content": error,
                })
            except Exception:
                self.disconnect(session_id)

    async def send_task_progress(self, session_id: str, task_id: str, progress: dict):
        """推送任务进度"""
        ws = self.active_connections.get(session_id)
        if ws:
            try:
                await ws.send_json({
                    "type": "task_progress",
                    "task_id": task_id,
                    **progress,
                })
            except Exception:
                self.disconnect(session_id)

    def is_connected(self, session_id: str) -> bool:
        return session_id in self.active_connections


# 全局连接管理器
ws_manager = ConnectionManager()
