"""
会话管理模块

基于session_id管理多轮对话上下文。
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading


class SessionStore:
    """会话存储 - 支持多轮对话"""

    def __init__(self, ttl_minutes: int = 30, max_history: int = 20):
        self.sessions: Dict[str, dict] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_history = max_history
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str) -> dict:
        """获取或创建会话"""
        with self._lock:
            self._cleanup_expired()
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "messages": [],
                    "created_at": datetime.now(),
                    "last_active": datetime.now(),
                    "metadata": {},
                }
            return self.sessions[session_id]

    def get_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.get("messages", [])

    def add_message(self, session_id: str, role: str, content: str):
        """添加一条消息到会话历史"""
        session = self.get_or_create(session_id)
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        session["last_active"] = datetime.now()

        # 超出最大历史时截断
        if len(session["messages"]) > self.max_history:
            session["messages"] = session["messages"][-self.max_history:]

    def build_context(self, session_id: str, max_turns: int = 5) -> List[Dict]:
        """构建多轮对话上下文（最近N轮）"""
        history = self.get_history(session_id)
        return history[-max_turns * 2:]

    def set_metadata(self, session_id: str, key: str, value):
        """设置会话元数据"""
        session = self.get_or_create(session_id)
        session["metadata"][key] = value

    def get_metadata(self, session_id: str, key: str, default=None):
        """获取会话元数据"""
        session = self.sessions.get(session_id)
        if not session:
            return default
        return session.get("metadata", {}).get(key, default)

    def delete_session(self, session_id: str):
        """删除会话"""
        with self._lock:
            self.sessions.pop(session_id, None)

    def _cleanup_expired(self):
        """清理过期会话"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_active"] > self.ttl
        ]
        for sid in expired:
            del self.sessions[sid]


# 全局会话存储实例
session_store = SessionStore()
