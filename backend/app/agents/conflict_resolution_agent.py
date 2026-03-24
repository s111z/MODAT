"""
冲突裁决Agent

对知识库与网络搜索的多源结果进行一致性分析和冲突裁决。
"""

from typing import Any, List, Dict

from .base_agent import BaseAgent


class ConflictResolutionAgent(BaseAgent):
    """冲突裁决Agent"""

    def __init__(self, llm_client=None):
        super().__init__("conflict_resolution", llm_client)

    async def execute(self, input_data: dict) -> Any:
        knowledge_results = input_data.get("knowledge_results", [])
        web_results = input_data.get("web_results", [])
        query = input_data.get("query", "")
        return self.resolve(query, knowledge_results, web_results)

    def resolve(
        self,
        query: str,
        knowledge_results: List[Dict],
        web_results: List[Dict],
    ) -> dict:
        """裁决多源信息冲突"""
        # 仅单一来源时不需要裁决
        if not knowledge_results and not web_results:
            return {
                "resolved_context": "",
                "conflict_found": False,
                "summary": "未找到任何检索结果",
            }

        if not web_results:
            return {
                "resolved_context": self._format_results("知识库", knowledge_results),
                "conflict_found": False,
                "summary": "仅使用知识库结果",
            }

        if not knowledge_results:
            return {
                "resolved_context": self._format_results("网络搜索", web_results),
                "conflict_found": False,
                "summary": "仅使用网络搜索结果",
            }

        # 多源都有结果，使用LLM进行裁决
        try:
            kb_text = self._format_results("知识库", knowledge_results)
            web_text = self._format_results("网络搜索", web_results)

            result = self.llm_generate_json(
                prompt=f"用户问题: {query}",
                context=f"知识库检索结果:\n{kb_text}\n\n网络搜索结果:\n{web_text}",
                system_message="""你是信息一致性裁决专家。分析两个来源的检索结果，进行冲突裁决。

返回JSON格式：
{
    "conflict_found": true/false,
    "consistent_info": "两个来源一致的信息摘要",
    "conflicts": [{"topic": "冲突主题", "knowledge_says": "知识库观点", "web_says": "网络观点", "resolution": "裁决结论"}],
    "resolved_context": "综合裁决后的最终上下文（供回复生成使用）",
    "summary": "裁决概要"
}

裁决原则：
- 知识库结果优先级更高（内部权威数据）
- 网络结果用于补充和交叉验证
- 冲突时标注两方观点并给出裁决理由"""
            )
            return result
        except Exception as e:
            self.logger.error(f"LLM裁决失败，使用合并模式: {e}")
            # 降级：简单合并
            merged = f"知识库结果:\n{kb_text}\n\n网络搜索结果:\n{web_text}"
            return {
                "resolved_context": merged,
                "conflict_found": False,
                "summary": "裁决失败，已合并所有结果",
            }

    def _format_results(self, source_name: str, results: List[Dict]) -> str:
        """格式化结果列表为文本"""
        parts = []
        for i, r in enumerate(results, 1):
            content = r.get("content", "")
            title = r.get("title", r.get("document", ""))
            if title:
                parts.append(f"{i}. [{title}] {content}")
            else:
                parts.append(f"{i}. {content}")
        return "\n".join(parts)
