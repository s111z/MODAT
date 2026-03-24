"""
质询/自查Agent

对审核草稿进行自查，检查逻辑一致性和遗漏。
"""

from typing import Any

from .base_agent import BaseAgent


class InquiryAgent(BaseAgent):
    """质询/自查Agent"""

    def __init__(self, llm_client=None):
        super().__init__("inquiry", llm_client)

    async def execute(self, input_data: dict) -> Any:
        review_draft = input_data.get("review_draft", "")
        original_doc_summary = input_data.get("original_doc_summary", "")
        return self.self_check(review_draft, original_doc_summary)

    def self_check(self, review_draft: str, original_doc_summary: str = "") -> dict:
        """对审核结果进行自查"""
        try:
            context_parts = [f"审核草稿:\n{review_draft}"]
            if original_doc_summary:
                context_parts.append(f"原始文档摘要:\n{original_doc_summary[:2000]}")

            result = self.llm_generate_json(
                prompt="请对以上审核草稿进行自查",
                context="\n\n".join(context_parts),
                system_message="""你是审核质量检查专家。对审核草稿进行自查，检查以下方面：

1. 遗漏检查：是否有重要审核要点被遗漏
2. 逻辑一致性：各部分结论是否存在矛盾
3. 引用准确性：引用的法规条款是否正确
4. 建议完整性：改进建议是否具体可执行

返回JSON格式：
{
    "issues_found": true/false,
    "issues": [{"type": "遗漏/矛盾/引用错误/建议不完整", "description": "具体问题", "suggestion": "修正建议"}],
    "quality_score": 0-100,
    "summary": "自查概要"
}"""
            )
            return result
        except Exception as e:
            self.logger.error(f"自查失败: {e}")
            return {
                "issues_found": False,
                "issues": [],
                "quality_score": 0,
                "summary": f"自查过程出错: {str(e)}",
            }
