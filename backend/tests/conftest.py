"""
全局测试配置和共享Fixtures
"""

import sys
import os
import json
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# 确保 app/ 在 sys.path 中
APP_DIR = str(Path(__file__).resolve().parent.parent / "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


# ===== Mock 类 =====

class MockLLMClient:
    """统一Mock LLM客户端"""

    def __init__(self, response="mock response"):
        self.response = response
        self.call_count = 0
        self.last_prompt = None
        self.last_context = None
        self.call_log = []

    def generate_response(self, prompt, context=None, system_message=None):
        self.call_count += 1
        self.last_prompt = prompt
        self.last_context = context
        self.call_log.append({
            "prompt": prompt,
            "context": context,
            "system_message": system_message,
        })
        if callable(self.response):
            return self.response(prompt, context, system_message)
        return self.response


class MockLLMJsonClient(MockLLMClient):
    """返回JSON字符串的Mock LLM"""

    def __init__(self, json_data: dict):
        self._json_data = json_data
        super().__init__(response=json.dumps(json_data, ensure_ascii=False))

    @property
    def json_data(self):
        return self._json_data

    @json_data.setter
    def json_data(self, value):
        self._json_data = value
        self.response = json.dumps(value, ensure_ascii=False)


class MockLLMFailClient(MockLLMClient):
    """总是抛异常的Mock LLM"""

    def generate_response(self, prompt, context=None, system_message=None):
        self.call_count += 1
        raise Exception("LLM service unavailable")


class MockLLMSequenceClient(MockLLMClient):
    """按顺序返回不同响应的Mock LLM，用于多轮调用测试"""

    def __init__(self, responses: list):
        super().__init__()
        self._responses = responses
        self._index = 0

    def generate_response(self, prompt, context=None, system_message=None):
        self.call_count += 1
        self.last_prompt = prompt
        self.last_context = context
        if self._index < len(self._responses):
            resp = self._responses[self._index]
            self._index += 1
        else:
            resp = self._responses[-1]
        if isinstance(resp, dict):
            return json.dumps(resp, ensure_ascii=False)
        return resp


class MockDBManager:
    """Mock向量数据库"""

    def __init__(self, results=None):
        self.results = results or []
        self.call_count = 0
        self.last_query = None

    def search(self, query, top_k=3, filter_meta=None):
        self.call_count += 1
        self.last_query = query
        return self.results[:top_k]


class MockDBFailManager:
    """总是抛异常的Mock向量数据库"""

    def search(self, query, top_k=3, filter_meta=None):
        raise Exception("Database connection failed")


class MockSearchClient:
    """Mock搜索客户端"""

    def __init__(self, results=None):
        self.results = results or []
        self.call_count = 0
        self.last_query = None

    def search(self, query, max_results=5):
        self.call_count += 1
        self.last_query = query
        return self.results[:max_results]


class MockSearchFailClient:
    """总是抛异常的Mock搜索客户端"""

    def search(self, query, max_results=5):
        raise Exception("Search service unavailable")


# ===== Fixtures =====

@pytest.fixture
def mock_llm():
    return MockLLMClient()

@pytest.fixture
def mock_llm_fail():
    return MockLLMFailClient()

@pytest.fixture
def mock_llm_json():
    """可配置JSON响应的MockLLM, 默认返回空dict"""
    return MockLLMJsonClient({})

@pytest.fixture
def mock_llm_sequence():
    """按顺序返回多个响应的MockLLM"""
    return MockLLMSequenceClient(["response1", "response2", "response3"])

@pytest.fixture
def mock_db_manager():
    return MockDBManager(results=[
        {"id": "1", "content": "测试文档内容1", "metadata": {"source": "test.pdf"}, "distance": 0.1},
        {"id": "2", "content": "测试文档内容2", "metadata": {"source": "test.pdf"}, "distance": 0.2},
        {"id": "3", "content": "测试文档内容3", "metadata": {"source": "test2.pdf"}, "distance": 0.3},
    ])

@pytest.fixture
def mock_db_empty():
    return MockDBManager(results=[])

@pytest.fixture
def mock_db_fail():
    return MockDBFailManager()

@pytest.fixture
def mock_search_client():
    return MockSearchClient(results=[
        {"title": "搜索结果1", "url": "https://example.com/1", "content": "网络内容1", "source": "duckduckgo"},
        {"title": "搜索结果2", "url": "https://example.com/2", "content": "网络内容2", "source": "duckduckgo"},
    ])

@pytest.fixture
def mock_search_empty():
    return MockSearchClient(results=[])

@pytest.fixture
def mock_search_fail():
    return MockSearchFailClient()

@pytest.fixture
def sample_pdf_path():
    """返回测试PDF路径"""
    fixtures = Path(__file__).parent / "fixtures"
    pdf = fixtures / "test_sample.pdf"
    if pdf.exists():
        return str(pdf)
    return None

@pytest.fixture
def sample_txt_path(tmp_path):
    """创建临时txt文件"""
    txt = tmp_path / "test_doc.txt"
    txt.write_text(
        "这是一个测试文档。\n包含多行内容。\n用于测试文档解析功能。\n\n"
        "第二段落。讨论墨西哥联邦劳动法的相关规定。\n"
        "雇佣关系应当遵守法律规定的最低工资标准。",
        encoding="utf-8",
    )
    return str(txt)

@pytest.fixture
def sample_txt_with_pii(tmp_path):
    """创建包含PII的临时txt文件"""
    txt = tmp_path / "pii_doc.txt"
    txt.write_text(
        "联系人张三，手机号13912345678，"
        "邮箱zhangsan@company.com，"
        "身份证号110101199001011234。",
        encoding="utf-8",
    )
    return str(txt)

@pytest.fixture
def test_client():
    """FastAPI TestClient"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)

@pytest.fixture
def qa_state_factory():
    """QAState工厂，快速创建测试用state"""
    def _make(query="测试问题", session_id="test-session", **overrides):
        state = {
            "query": query,
            "session_id": session_id,
            "desensitized_query": "",
            "pii_mapping": {},
            "intent": "",
            "deep_mode": False,
            "processed_queries": [],
            "query_type": "simple",
            "knowledge_results": [],
            "web_results": [],
            "resolved_context": "",
            "conflict_found": False,
            "conflict_summary": "",
            "history": [],
            "response": "",
            "steps": [],
        }
        state.update(overrides)
        return state
    return _make

@pytest.fixture
def review_state_factory(sample_txt_path):
    """ReviewState工厂，快速创建测试用state"""
    def _make(query="请审核此方案", filepath=None, **overrides):
        state = {
            "query": query,
            "session_id": "test-review-session",
            "filepath": filepath or sample_txt_path,
            "desensitized_query": "",
            "pii_mapping": {},
            "intent": "document_review",
            "has_history": False,
            "has_policy_change": True,
            "doc_info": {},
            "doc_text": "",
            "structured_data": {},
            "review_queries": [],
            "review_dimensions": [],
            "knowledge_results": [],
            "web_results": [],
            "resolved_context": "",
            "conflict_found": False,
            "conflict_summary": "",
            "inquiry_result": {},
            "rewrite_suggestions": "",
            "review_report": "",
            "response": "",
            "steps": [],
        }
        state.update(overrides)
        return state
    return _make
