"""方案审核流式事件工具。"""

from copy import deepcopy
from typing import Any, Dict, List, Optional


REVIEW_STEPS: List[Dict[str, Any]] = [
    {
        "id": "doc-analysis",
        "name": "读取文档",
        "icon": "",
        "status": "pending",
        "details": {"summary": {}},
        "logs": [],
    },
    {
        "id": "schema-extraction",
        "name": "提取关键信息",
        "icon": "",
        "status": "pending",
        "details": {"fields": []},
        "logs": [],
    },
    {
        "id": "query-construction",
        "name": "构建查询问题",
        "icon": "",
        "status": "pending",
        "details": {"queries": []},
        "logs": [],
    },
    {
        "id": "multi-source-pk",
        "name": "多源检索与裁决",
        "icon": "",
        "status": "pending",
        "details": {"analysis": [], "knowledgeResults": [], "webResults": []},
        "logs": [],
    },
    {
        "id": "quality-check",
        "name": "审核自查",
        "icon": "",
        "status": "pending",
        "details": {"checks": []},
        "logs": [],
    },
    {
        "id": "plan-rewrite",
        "name": "方案优化",
        "icon": "",
        "status": "pending",
        "details": {"sections": []},
        "logs": [],
    },
    {
        "id": "report-generation",
        "name": "生成审核报告",
        "icon": "",
        "status": "pending",
        "progress": 0,
        "details": {"sections": ["审核概要", "风险分析", "问题建议", "审核结论"]},
        "logs": [],
    },
]

NODE_TO_STEP_ID: Dict[str, Optional[str]] = {
    "desensitize": None,
    "check_history": None,
    "parse_document": "doc-analysis",
    "struct_extract": "schema-extraction",
    "build_queries": "query-construction",
    "multi_source_search": "multi-source-pk",
    "conflict_resolve": "multi-source-pk",
    "inquiry_check": "quality-check",
    "generate_review": "report-generation",
}

NODE_MESSAGES: Dict[str, str] = {
    "desensitize": "正在进行信息脱敏...",
    "check_history": "正在检查历史审核记录...",
    "parse_document": "正在解析文档...",
    "struct_extract": "正在提取文档关键信息...",
    "build_queries": "正在构建审核查询问题...",
    "multi_source_search": "正在进行知识库和网络多源检索...",
    "conflict_resolve": "正在进行多源信息裁决...",
    "inquiry_check": "正在进行审核自查...",
    "generate_review": "正在生成方案优化建议和审核报告...",
}

NODE_DONE_MESSAGES: Dict[str, str] = {
    "desensitize": "信息脱敏完成",
    "check_history": "历史审核记录检查完成",
    "parse_document": "文档解析完成",
    "struct_extract": "关键信息提取完成",
    "build_queries": "审核查询问题构建完成",
    "multi_source_search": "多源检索完成",
    "conflict_resolve": "多源信息裁决完成",
    "inquiry_check": "审核自查完成",
    "generate_review": "审核报告生成完成",
}


def build_workflow_init_event() -> Dict[str, Any]:
    return {"type": "workflow_init", "steps": deepcopy(REVIEW_STEPS)}


def build_node_start_event(node_name: str, step_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not step_id:
        return None
    return {
        "type": "node_start",
        "stepId": step_id,
        "node": node_name,
        "message": NODE_MESSAGES.get(node_name, f"正在执行 {node_name}..."),
    }


def build_step_patch_event(step_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "step_patch", "stepId": step_id, "patch": patch}


def build_node_log_event(step_id: str, message: str) -> Dict[str, Any]:
    return {"type": "node_log", "stepId": step_id, "message": message}


def build_command_log_event(
    message: str,
    level: str = "INFO",
    logger: str = "console",
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "type": "command_log",
        "level": level,
        "logger": logger,
        "timestamp": timestamp,
        "message": message,
    }


def build_document_patch_event(content: str, doc_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "type": "document_patch",
        "content": content or "",
        "documentInfo": doc_info or {},
    }
