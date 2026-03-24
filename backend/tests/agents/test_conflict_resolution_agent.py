"""ConflictResolutionAgent单元测试"""

import pytest
from agents.conflict_resolution_agent import ConflictResolutionAgent


@pytest.mark.unit
class TestConflictResolutionAgent:

    def _kb_results(self):
        return [{"content": "知识库内容", "document": "法规文件"}]

    def _web_results(self):
        return [{"content": "网络内容", "title": "新闻报道"}]

    def test_both_empty(self, mock_llm):
        agent = ConflictResolutionAgent(llm_client=mock_llm)
        result = agent.resolve("测试", [], [])
        assert result["conflict_found"] is False
        assert "未找到" in result["summary"]

    def test_only_knowledge(self, mock_llm):
        agent = ConflictResolutionAgent(llm_client=mock_llm)
        result = agent.resolve("测试", self._kb_results(), [])
        assert result["conflict_found"] is False
        assert "知识库" in result["summary"]
        assert "知识库内容" in result["resolved_context"]

    def test_only_web(self, mock_llm):
        agent = ConflictResolutionAgent(llm_client=mock_llm)
        result = agent.resolve("测试", [], self._web_results())
        assert result["conflict_found"] is False
        assert "网络" in result["summary"]

    def test_both_sources_llm_success(self, mock_llm_json):
        mock_llm_json.json_data = {
            "conflict_found": True,
            "consistent_info": "一致信息",
            "conflicts": [{"topic": "主题", "resolution": "结论"}],
            "resolved_context": "综合上下文",
            "summary": "存在冲突",
        }
        agent = ConflictResolutionAgent(llm_client=mock_llm_json)
        result = agent.resolve("测试", self._kb_results(), self._web_results())
        assert result["conflict_found"] is True
        assert result["resolved_context"] == "综合上下文"

    def test_both_sources_llm_fail(self, mock_llm_fail):
        agent = ConflictResolutionAgent(llm_client=mock_llm_fail)
        result = agent.resolve("测试", self._kb_results(), self._web_results())
        assert result["conflict_found"] is False
        assert "裁决失败" in result["summary"]
        assert "知识库内容" in result["resolved_context"]
        assert "网络内容" in result["resolved_context"]

    def test_format_results(self, mock_llm):
        agent = ConflictResolutionAgent(llm_client=mock_llm)
        text = agent._format_results("测试来源", [
            {"content": "内容A", "title": "标题A"},
            {"content": "内容B"},
        ])
        assert "标题A" in text
        assert "内容B" in text
