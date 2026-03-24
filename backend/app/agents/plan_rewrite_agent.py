"""
方案重写Agent

根据审核结果对方案提出修改建议或生成修订版本。
"""

from typing import Any

from .base_agent import BaseAgent


class PlanRewriteAgent(BaseAgent):
    """方案重写Agent"""

    def __init__(self, llm_client=None):
        super().__init__("plan_rewrite", llm_client)

    async def execute(self, input_data: dict) -> Any:
        original_text = input_data.get("original_text", "")
        review_findings = input_data.get("review_findings", "")
        return self.rewrite(original_text, review_findings)

    def rewrite(self, original_text: str, review_findings: str) -> dict:
        """根据审核结果生成修改建议"""
        try:
            response = self.llm_generate(
                prompt="请根据审核发现生成修改建议",
                context=f"审核发现:\n{review_findings}\n\n原始方案(摘要):\n{original_text[:3000]}",
                system_message="""你是方案修改专家。根据审核发现的问题，生成具体的修改建议。

要求：
- 对每个问题给出具体的修改方案
- 修改建议要可操作、可执行
- 标注修改的优先级（高/中/低）
- 格式清晰，使用编号列表"""
            )
            return {"suggestions": response, "success": True}
        except Exception as e:
            self.logger.error(f"方案重写失败: {e}")
            return {"suggestions": "", "success": False, "error": str(e)}
