"""
意图识别Agent

对用户输入进行意图分类：
- knowledge_qa: 知识问答
- document_review: 方案审核
- chitchat: 寒暄闲聊

同时判断是否需要开启深度思考模式。
"""

from typing import Any

from .base_agent import BaseAgent


class IntentAgent(BaseAgent):
    """意图识别Agent"""

    DEEP_KEYWORDS = ["详细", "深入", "分析", "研究", "对比", "比较", "区别", "为什么", "原因"]

    def __init__(self, llm_client=None):
        super().__init__("intent", llm_client)

    async def execute(self, input_data: dict) -> Any:
        query = input_data.get("query", "")
        has_file = input_data.get("has_file", False)
        return self.classify(query, has_file)

    def classify(self, query: str, has_file: bool = False) -> dict:
        """意图分类"""
        # 有文件上传 → 方案审核
        if has_file:
            return {
                "intent": "document_review",
                "deep_mode": True,
            }

        # 使用LLM进行意图分类
        try:
            result = self.llm_generate_json(
                prompt=query,
                system_message="""你是一个意图分类专家。根据用户输入判断意图类别。
返回JSON格式，不要有其他内容：
{"intent": "knowledge_qa|chitchat", "deep_mode": true|false}

分类规则：
- knowledge_qa: 用户在询问知识性问题、寻求专业解答
- chitchat: 用户在打招呼、闲聊、感谢等非知识性对话

deep_mode规则：
- true: 问题复杂，需要多源检索和深度分析
- false: 问题简单，可以直接从知识库回答"""
            )
            return result
        except Exception:
            # LLM调用失败时使用规则判断
            return self._rule_based_classify(query)

    def _rule_based_classify(self, query: str) -> dict:
        """基于规则的降级分类"""
        chitchat_patterns = ["你好", "谢谢", "再见", "嗨", "hello", "hi", "感谢", "辛苦"]
        query_lower = query.lower().strip()

        for pattern in chitchat_patterns:
            if pattern in query_lower:
                return {"intent": "chitchat", "deep_mode": False}

        deep_mode = any(kw in query for kw in self.DEEP_KEYWORDS)
        return {"intent": "knowledge_qa", "deep_mode": deep_mode}
