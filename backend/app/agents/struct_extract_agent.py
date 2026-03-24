"""
结构化抽取Agent

根据Schema定义从文档中提取结构化信息。
用于方案审核流程的预处理阶段。
"""

from typing import Any

from .base_agent import BaseAgent


# 默认审核Schema
DEFAULT_REVIEW_SCHEMA = {
    "company_name": "公司名称",
    "project_name": "项目/方案名称",
    "industry": "所属行业",
    "location": "涉及地区/国家",
    "key_regulations": "涉及的法规/标准",
    "risk_points": "风险点描述",
    "financial_data": "关键财务数据",
    "timeline": "时间节点/计划",
    "stakeholders": "相关方",
}


class StructExtractAgent(BaseAgent):
    """结构化抽取Agent"""

    def __init__(self, llm_client=None):
        super().__init__("struct_extract", llm_client)

    async def execute(self, input_data: dict) -> Any:
        text = input_data.get("text", "")
        schema = input_data.get("schema", DEFAULT_REVIEW_SCHEMA)
        return self.extract(text, schema)

    def extract(self, text: str, schema: dict = None) -> dict:
        """从文档中提取结构化信息"""
        schema = schema or DEFAULT_REVIEW_SCHEMA

        # 文档过长时截断
        max_len = 6000
        doc_text = text[:max_len] if len(text) > max_len else text

        schema_desc = "\n".join([f"- {k}: {v}" for k, v in schema.items()])

        try:
            result = self.llm_generate_json(
                prompt=f"文档内容:\n{doc_text}",
                system_message=f"""你是文档结构化信息提取专家。从文档中提取以下字段信息。

需要提取的字段：
{schema_desc}

返回JSON格式，如果某个字段在文档中找不到，值设为null。
只返回JSON，不要有其他内容。"""
            )
            return {"structured_data": result, "success": True}
        except Exception as e:
            self.logger.error(f"结构化抽取失败: {e}")
            return {"structured_data": {}, "success": False, "error": str(e)}
