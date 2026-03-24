"""IntentAgent单元测试"""

import pytest
from agents.intent_agent import IntentAgent


@pytest.mark.unit
class TestIntentAgent:

    # --- has_file 直接判定 ---

    def test_has_file_returns_review(self, mock_llm):
        agent = IntentAgent(llm_client=mock_llm)
        result = agent.classify("任意内容", has_file=True)
        assert result["intent"] == "document_review"
        assert result["deep_mode"] is True

    # --- 规则降级测试 ---

    def test_rule_chitchat_nihao(self, mock_llm_fail):
        agent = IntentAgent(llm_client=mock_llm_fail)
        result = agent.classify("你好")
        assert result["intent"] == "chitchat"
        assert result["deep_mode"] is False

    def test_rule_chitchat_thanks(self, mock_llm_fail):
        agent = IntentAgent(llm_client=mock_llm_fail)
        result = agent.classify("谢谢你的帮助")
        assert result["intent"] == "chitchat"

    def test_rule_chitchat_hello(self, mock_llm_fail):
        agent = IntentAgent(llm_client=mock_llm_fail)
        result = agent.classify("Hello")
        assert result["intent"] == "chitchat"

    def test_rule_simple_qa(self, mock_llm_fail):
        agent = IntentAgent(llm_client=mock_llm_fail)
        result = agent.classify("墨西哥劳动法规定")
        assert result["intent"] == "knowledge_qa"
        assert result["deep_mode"] is False

    def test_rule_deep_mode(self, mock_llm_fail):
        agent = IntentAgent(llm_client=mock_llm_fail)
        result = agent.classify("详细分析墨西哥劳动法")
        assert result["intent"] == "knowledge_qa"
        assert result["deep_mode"] is True

    def test_rule_deep_keywords(self, mock_llm_fail):
        agent = IntentAgent(llm_client=mock_llm_fail)
        for keyword in ["深入", "分析", "研究", "对比", "为什么"]:
            result = agent.classify(f"请{keyword}这个问题")
            assert result["deep_mode"] is True, f"关键词'{keyword}'应触发深度模式"

    # --- LLM分类测试 ---

    def test_llm_classify_success(self, mock_llm_json):
        mock_llm_json.json_data = {"intent": "knowledge_qa", "deep_mode": False}
        agent = IntentAgent(llm_client=mock_llm_json)
        result = agent.classify("测试问题")
        assert result["intent"] == "knowledge_qa"
        assert result["deep_mode"] is False
