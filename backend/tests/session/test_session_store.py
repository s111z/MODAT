"""SessionStore单元测试"""

import pytest
import time
from session.session_store import SessionStore


@pytest.mark.unit
class TestSessionStore:

    def setup_method(self):
        self.store = SessionStore(ttl_minutes=1, max_history=5)

    def test_get_or_create_new(self):
        session = self.store.get_or_create("s1")
        assert session["messages"] == []
        assert "created_at" in session

    def test_get_or_create_existing(self):
        self.store.get_or_create("s1")
        self.store.add_message("s1", "user", "hello")
        session = self.store.get_or_create("s1")
        assert len(session["messages"]) == 1

    def test_add_message(self):
        self.store.add_message("s1", "user", "问题")
        self.store.add_message("s1", "assistant", "回答")
        history = self.store.get_history("s1")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_build_context(self):
        for i in range(10):
            self.store.add_message("s1", "user", f"q{i}")
            self.store.add_message("s1", "assistant", f"a{i}")
        context = self.store.build_context("s1", max_turns=2)
        # 最近2轮 = 4条消息
        assert len(context) == 4

    def test_max_history_truncation(self):
        for i in range(10):
            self.store.add_message("s1", "user", f"msg{i}")
        history = self.store.get_history("s1")
        assert len(history) == 5  # max_history=5

    def test_get_history_nonexistent(self):
        assert self.store.get_history("not_exist") == []

    def test_set_get_metadata(self):
        self.store.set_metadata("s1", "key1", "value1")
        assert self.store.get_metadata("s1", "key1") == "value1"
        assert self.store.get_metadata("s1", "missing", "default") == "default"

    def test_get_metadata_nonexistent_session(self):
        assert self.store.get_metadata("not_exist", "key") is None

    def test_delete_session(self):
        self.store.add_message("s1", "user", "hello")
        self.store.delete_session("s1")
        assert self.store.get_history("s1") == []

    def test_delete_nonexistent(self):
        # 不应抛异常
        self.store.delete_session("not_exist")
