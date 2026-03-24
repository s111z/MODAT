"""
历史方案审核Agent

检查是否有历史审核记录，判断政策是否有变化。
"""

from typing import Any

from .base_agent import BaseAgent


class HistoryReviewAgent(BaseAgent):
    """历史方案审核Agent"""

    def __init__(self, llm_client=None):
        super().__init__("history_review", llm_client)

    async def execute(self, input_data: dict) -> Any:
        doc_info = input_data.get("doc_info", {})
        return self.check_history(doc_info)

    def check_history(self, doc_info: dict) -> dict:
        """检查是否有历史审核记录"""
        # TODO: 接入业务数据库查询历史审核记录
        # 当前版本返回无历史记录，总是执行完整审核
        return {
            "has_history": False,
            "has_policy_change": True,
            "history_records": [],
            "recommendation": "执行完整审核",
        }
