"""WebSearchAgent单元测试"""

import pytest
from agents.web_search_agent import WebSearchAgent


@pytest.mark.unit
class TestWebSearchAgent:

    def test_search_normal(self, mock_llm, mock_search_client):
        agent = WebSearchAgent(llm_client=mock_llm, search_client=mock_search_client)
        results = agent.search("测试查询", max_results=2)
        assert len(results) == 2
        assert mock_search_client.call_count == 1

    def test_search_empty(self, mock_llm, mock_search_empty):
        agent = WebSearchAgent(llm_client=mock_llm, search_client=mock_search_empty)
        results = agent.search("不存在")
        assert results == []

    def test_search_exception(self, mock_llm):
        fail_client = type("FailSearch", (), {
            "search": lambda *a, **kw: (_ for _ in ()).throw(Exception("Search error"))
        })()
        agent = WebSearchAgent(llm_client=mock_llm, search_client=fail_client)
        results = agent.search("测试")
        assert results == []

    def test_format_context(self, mock_llm, mock_search_client):
        agent = WebSearchAgent(llm_client=mock_llm, search_client=mock_search_client)
        text = agent.format_context(mock_search_client.results)
        assert "网络来源1" in text
        assert "搜索结果1" in text
        assert "example.com" in text

    def test_format_context_empty(self, mock_llm, mock_search_client):
        agent = WebSearchAgent(llm_client=mock_llm, search_client=mock_search_client)
        assert agent.format_context([]) == ""
