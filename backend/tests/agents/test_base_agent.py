"""BaseAgent单元测试"""

import pytest
import asyncio
import json
from agents.base_agent import BaseAgent


class ConcreteAgent(BaseAgent):
    """测试用的具体Agent实现"""

    def __init__(self, llm_client=None, should_fail=False):
        super().__init__("test_agent", llm_client)
        self.should_fail = should_fail

    async def execute(self, input_data: dict):
        if self.should_fail:
            raise ValueError("测试异常")
        return {"result": "ok", "input": input_data}


@pytest.mark.unit
class TestBaseAgent:

    def test_run_success(self, mock_llm):
        agent = ConcreteAgent(llm_client=mock_llm)
        result = asyncio.get_event_loop().run_until_complete(
            agent.run({"key": "value"})
        )
        assert result["status"] == "success"
        assert result["agent"] == "test_agent"
        assert result["elapsed"] > 0
        assert result["data"]["result"] == "ok"

    def test_run_failure(self, mock_llm):
        agent = ConcreteAgent(llm_client=mock_llm, should_fail=True)
        result = asyncio.get_event_loop().run_until_complete(
            agent.run({"key": "value"})
        )
        assert result["status"] == "error"
        assert "测试异常" in result["error"]

    def test_llm_generate(self, mock_llm):
        agent = ConcreteAgent(llm_client=mock_llm)
        result = agent.llm_generate("test prompt")
        assert result == "mock response"
        assert mock_llm.call_count == 1

    def test_llm_generate_json_plain(self, mock_llm):
        mock_llm.response = '{"key": "value"}'
        agent = ConcreteAgent(llm_client=mock_llm)
        result = agent.llm_generate_json("test")
        assert result == {"key": "value"}

    def test_llm_generate_json_codeblock(self, mock_llm):
        mock_llm.response = '```json\n{"key": "value"}\n```'
        agent = ConcreteAgent(llm_client=mock_llm)
        result = agent.llm_generate_json("test")
        assert result == {"key": "value"}

    def test_llm_generate_json_invalid(self, mock_llm):
        mock_llm.response = "not json"
        agent = ConcreteAgent(llm_client=mock_llm)
        with pytest.raises(json.JSONDecodeError):
            agent.llm_generate_json("test")
