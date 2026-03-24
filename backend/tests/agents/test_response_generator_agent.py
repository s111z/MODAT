"""ResponseGeneratorAgent单元测试"""

import pytest
from agents.response_generator_agent import ResponseGeneratorAgent


@pytest.mark.unit
class TestResponseGeneratorAgent:

    def test_chitchat_success(self, mock_llm):
        mock_llm.response = "你好！很高兴见到你"
        agent = ResponseGeneratorAgent(llm_client=mock_llm)
        result = agent.generate("你好", "", intent="chitchat")
        assert result["type"] == "chitchat"
        assert "你好" in result["response"]

    def test_chitchat_llm_fail(self, mock_llm_fail):
        agent = ResponseGeneratorAgent(llm_client=mock_llm_fail)
        result = agent.generate("你好", "", intent="chitchat")
        assert result["type"] == "chitchat"
        assert "你好" in result["response"]

    def test_qa_success(self, mock_llm):
        mock_llm.response = "根据法规规定..."
        agent = ResponseGeneratorAgent(llm_client=mock_llm)
        result = agent.generate("劳动法问题", "参考上下文", intent="knowledge_qa")
        assert result["type"] == "knowledge_qa"
        assert "法规" in result["response"]

    def test_qa_with_history(self, mock_llm):
        mock_llm.response = "基于之前的对话..."
        agent = ResponseGeneratorAgent(llm_client=mock_llm)
        history = [
            {"role": "user", "content": "之前的问题"},
            {"role": "assistant", "content": "之前的回答"},
        ]
        result = agent.generate("后续问题", "上下文", history=history)
        assert result["type"] == "knowledge_qa"
        # 确认LLM收到了历史context
        assert "对话历史" in mock_llm.last_context

    def test_qa_llm_fail(self, mock_llm_fail):
        agent = ResponseGeneratorAgent(llm_client=mock_llm_fail)
        result = agent.generate("问题", "上下文", intent="knowledge_qa")
        assert result["type"] == "error"
        assert "抱歉" in result["response"]
