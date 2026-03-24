"""
回复生成Agent

综合检索结果、冲突裁决和对话历史，生成最终回复。
"""

from typing import Any, List, Dict

from .base_agent import BaseAgent


class ResponseGeneratorAgent(BaseAgent):
    """回复生成Agent"""

    def __init__(self, llm_client=None):
        super().__init__("response_generator", llm_client)

    async def execute(self, input_data: dict) -> Any:
        query = input_data.get("query", "")
        context = input_data.get("context", "")
        intent = input_data.get("intent", "knowledge_qa")
        history = input_data.get("history", [])
        return self.generate(query, context, intent, history)

    def generate(
        self,
        query: str,
        context: str,
        intent: str = "knowledge_qa",
        history: List[Dict] = None,
    ) -> dict:
        """生成回复"""
        if intent == "chitchat":
            return self._generate_chitchat(query)

        return self._generate_qa(query, context, history)

    def _generate_chitchat(self, query: str) -> dict:
        """生成寒暄回复"""
        try:
            response = self.llm_generate(
                prompt=query,
                system_message="你是一个友好的助手。用简短友好的方式回应用户的问候或闲聊。",
            )
            return {"response": response, "type": "chitchat"}
        except Exception:
            return {"response": "你好！有什么可以帮到你的吗？", "type": "chitchat"}

    def _generate_qa(
        self,
        query: str,
        context: str,
        history: List[Dict] = None,
    ) -> dict:
        """生成知识问答回复"""
        # 构建历史上下文
        history_text = ""
        if history:
            for msg in history[-6:]:  # 最近3轮
                role = "用户" if msg["role"] == "user" else "助手"
                history_text += f"{role}: {msg['content']}\n"

        full_context = ""
        if history_text:
            full_context += f"对话历史:\n{history_text}\n\n"
        if context:
            full_context += f"检索到的参考信息:\n{context}"

        try:
            response = self.llm_generate(
                prompt=query,
                context=full_context if full_context else None,
                system_message="""你是一个专业的文档评审和问答助手。请根据提供的参考信息回答用户问题。

回答要求：
- 基于提供的参考信息回答，不要凭空编造
- 如果参考信息不足以回答，明确告知用户
- 回答要结构化、条理清晰
- 引用来源时注明出处""",
            )
            return {"response": response, "type": "knowledge_qa"}
        except Exception as e:
            self.logger.error(f"回复生成失败: {e}")
            return {
                "response": "抱歉，生成回复时遇到问题，请稍后再试。",
                "type": "error",
            }
