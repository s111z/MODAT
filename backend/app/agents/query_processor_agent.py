"""
Query处理Agent

处理用户查询：
- 简单问答：query改写（同义词扩展、纠错）
- 复杂问答：分析拆解为多个子query
"""

from typing import Any

from .base_agent import BaseAgent


class QueryProcessorAgent(BaseAgent):
    """Query处理Agent"""

    def __init__(self, llm_client=None):
        super().__init__("query_processor", llm_client)

    async def execute(self, input_data: dict) -> Any:
        query = input_data.get("query", "")
        deep_mode = input_data.get("deep_mode", False)

        if deep_mode:
            return self.decompose(query)
        else:
            return self.rewrite(query)

    def rewrite(self, query: str) -> dict:
        """简单问答：query改写"""
        try:
            result = self.llm_generate_json(
                prompt=query,
                system_message="""你是一个query优化专家。对用户的查询进行改写优化，使其更适合知识库检索。
返回JSON格式：
{"type": "simple", "queries": ["优化后的query"]}

改写规则：
- 纠正明显的错别字
- 补充可能的同义词
- 使query更精确和完整
- 如果原始query已经很好，保持原样"""
            )
            return result
        except Exception:
            return {"type": "simple", "queries": [query]}

    def decompose(self, query: str) -> dict:
        """复杂问答：拆解为子query"""
        try:
            result = self.llm_generate_json(
                prompt=query,
                system_message="""你是一个问题分析专家。将复杂问题拆解为2-4个独立的子问题，每个子问题可以独立检索。
返回JSON格式：
{"type": "complex", "queries": ["子问题1", "子问题2", ...]}

拆解规则：
- 每个子问题应该是独立可回答的
- 子问题覆盖原始问题的所有方面
- 数量控制在2-4个"""
            )
            return result
        except Exception:
            return {"type": "complex", "queries": [query]}
