"""QueryProcessorAgent单元测试"""

import pytest
from agents.query_processor_agent import QueryProcessorAgent


@pytest.mark.unit
class TestQueryProcessorAgent:

    def test_rewrite_success(self, mock_llm_json):
        mock_llm_json.json_data = {"type": "simple", "queries": ["优化后的查询"]}
        agent = QueryProcessorAgent(llm_client=mock_llm_json)
        result = agent.rewrite("原始查询")
        assert result["type"] == "simple"
        assert len(result["queries"]) == 1

    def test_rewrite_llm_fail(self, mock_llm_fail):
        agent = QueryProcessorAgent(llm_client=mock_llm_fail)
        result = agent.rewrite("原始查询")
        assert result["type"] == "simple"
        assert result["queries"] == ["原始查询"]

    def test_decompose_success(self, mock_llm_json):
        mock_llm_json.json_data = {"type": "complex", "queries": ["子问题1", "子问题2"]}
        agent = QueryProcessorAgent(llm_client=mock_llm_json)
        result = agent.decompose("复杂问题")
        assert result["type"] == "complex"
        assert len(result["queries"]) == 2

    def test_decompose_llm_fail(self, mock_llm_fail):
        agent = QueryProcessorAgent(llm_client=mock_llm_fail)
        result = agent.decompose("复杂问题")
        assert result["type"] == "complex"
        assert result["queries"] == ["复杂问题"]
