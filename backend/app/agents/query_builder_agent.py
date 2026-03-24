"""
Query构造Agent

基于文档结构化数据，生成多维度审核查询。
用于方案审核流程的预处理阶段。
"""

from typing import Any, List

from .base_agent import BaseAgent


class QueryBuilderAgent(BaseAgent):
    """Query构造Agent"""

    def __init__(self, llm_client=None):
        super().__init__("query_builder", llm_client)

    async def execute(self, input_data: dict) -> Any:
        structured_data = input_data.get("structured_data", {})
        user_query = input_data.get("user_query", "")
        doc_summary = input_data.get("doc_summary", "")
        return self.build_queries(structured_data, user_query, doc_summary)

    def build_queries(
        self,
        structured_data: dict,
        user_query: str = "",
        doc_summary: str = "",
    ) -> dict:
        """根据结构化数据和用户需求生成审核查询"""
        try:
            context_parts = []
            if structured_data:
                context_parts.append(
                    "文档结构化信息:\n" +
                    "\n".join([f"- {k}: {v}" for k, v in structured_data.items() if v])
                )
            if doc_summary:
                context_parts.append(f"文档摘要:\n{doc_summary[:2000]}")

            context = "\n\n".join(context_parts)

            result = self.llm_generate_json(
                prompt=user_query or "请根据文档信息生成全面的审核查询",
                context=context,
                system_message="""你是方案审核专家。基于文档信息，生成多维度的审核查询列表。

每个查询应聚焦一个具体审核维度，例如：
- 法规合规性检查
- 财务数据合理性
- 风险点识别
- 行业标准符合性
- 时间节点可行性

返回JSON格式：
{"queries": ["查询1", "查询2", ...], "dimensions": ["维度1", "维度2", ...]}

查询数量控制在3-6个。"""
            )
            return result
        except Exception as e:
            self.logger.error(f"Query构造失败: {e}")
            # 降级：基于结构化数据生成基本查询
            return self._fallback_queries(structured_data, user_query)

    def _fallback_queries(self, structured_data: dict, user_query: str) -> dict:
        """降级查询生成"""
        queries = []
        dimensions = []

        if user_query:
            queries.append(user_query)
            dimensions.append("用户指定")

        if structured_data.get("key_regulations"):
            queries.append(f"关于{structured_data['key_regulations']}的最新要求和规定")
            dimensions.append("法规合规")

        if structured_data.get("location"):
            queries.append(f"{structured_data['location']}地区相关政策法规")
            dimensions.append("地区政策")

        if structured_data.get("risk_points"):
            queries.append(f"{structured_data['risk_points']}相关风险分析")
            dimensions.append("风险分析")

        if not queries:
            queries = ["方案整体合规性审核"]
            dimensions = ["综合审核"]

        return {"queries": queries, "dimensions": dimensions}
