"""
审核文档生成Agent

综合所有审核结果，生成完整的审核文档。
是方案审核流程的最终生成节点。
"""

from typing import Any

from .base_agent import BaseAgent


class ReviewDocGeneratorAgent(BaseAgent):
    """审核文档生成Agent"""

    def __init__(self, llm_client=None):
        super().__init__("review_doc_generator", llm_client)

    async def execute(self, input_data: dict) -> Any:
        doc_info = input_data.get("doc_info", {})
        structured_data = input_data.get("structured_data", {})
        resolved_context = input_data.get("resolved_context", "")
        conflict_summary = input_data.get("conflict_summary", "")
        inquiry_result = input_data.get("inquiry_result", {})
        rewrite_suggestions = input_data.get("rewrite_suggestions", "")
        return self.generate(
            doc_info, structured_data, resolved_context,
            conflict_summary, inquiry_result, rewrite_suggestions,
        )

    def generate(
        self,
        doc_info: dict,
        structured_data: dict,
        resolved_context: str,
        conflict_summary: str = "",
        inquiry_result: dict = None,
        rewrite_suggestions: str = "",
    ) -> dict:
        """生成完整审核文档"""
        # 构建审核上下文
        context_parts = []

        if doc_info:
            context_parts.append(
                f"文档信息: {doc_info.get('filename', '未知')}, "
                f"类型: {doc_info.get('file_type', '未知')}, "
                f"字符数: {doc_info.get('char_count', 0)}"
            )

        if structured_data:
            struct_text = "\n".join([
                f"- {k}: {v}" for k, v in structured_data.items() if v
            ])
            context_parts.append(f"结构化信息:\n{struct_text}")

        if resolved_context:
            context_parts.append(f"检索与裁决结果:\n{resolved_context}")

        if conflict_summary:
            context_parts.append(f"冲突裁决概要:\n{conflict_summary}")

        if inquiry_result and inquiry_result.get("issues"):
            issues_text = "\n".join([
                f"- [{i['type']}] {i['description']}"
                for i in inquiry_result["issues"]
            ])
            context_parts.append(f"自查发现的问题:\n{issues_text}")

        if rewrite_suggestions:
            context_parts.append(f"修改建议:\n{rewrite_suggestions}")

        context = "\n\n".join(context_parts)

        try:
            response = self.llm_generate(
                prompt="请生成完整的方案审核报告",
                context=context,
                system_message="""你是专业的方案审核报告撰写专家。基于提供的审核信息，生成一份结构完整的审核报告。

报告结构：
## 1. 审核概要
- 文档基本信息
- 审核范围和方法

## 2. 合规性审核结果
- 法规合规情况
- 标准符合情况

## 3. 风险分析
- 识别的风险点
- 风险等级评估

## 4. 多源信息交叉验证
- 知识库与网络搜索结果比对
- 信息一致性分析

## 5. 问题与建议
- 发现的问题清单
- 具体修改建议（按优先级排序）

## 6. 审核结论
- 总体评价
- 是否通过审核
- 后续建议

要求：语言专业严谨，结论有据可依。"""
            )
            return {"review_report": response, "success": True}
        except Exception as e:
            self.logger.error(f"审核文档生成失败: {e}")
            return {
                "review_report": "审核报告生成失败，请稍后重试。",
                "success": False,
                "error": str(e),
            }
