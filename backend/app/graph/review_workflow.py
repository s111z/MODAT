"""
方案审核工作流

对应架构图3：
信息脱敏 → 历史检查 → 文档解析 → 结构化抽取 → Query构造
→ 多源检索 → 冲突裁决 → 质询自查 → 审核文档生成

支持两种路径：
1. 有历史记录且无政策变化 → 复用历史结果
2. 无历史/有变化 → 执行完整审核流程
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from .review_state import ReviewState
from .review_nodes import (
    node_desensitize,
    node_check_history,
    node_parse_document,
    node_struct_extract,
    node_build_queries,
    node_multi_source_search,
    node_conflict_resolve,
    node_inquiry_check,
    node_generate_review,
)


def route_history(state: ReviewState) -> Literal["parse_document", "generate_review"]:
    """历史路由：有历史且无变化 → 复用，否则完整审核"""
    if state.get("has_history") and not state.get("has_policy_change"):
        return "generate_review"
    return "parse_document"


def create_review_workflow():
    """创建方案审核工作流"""
    workflow = StateGraph(ReviewState)

    # 添加节点
    workflow.add_node("desensitize", node_desensitize)
    workflow.add_node("check_history", node_check_history)
    workflow.add_node("parse_document", node_parse_document)
    workflow.add_node("struct_extract", node_struct_extract)
    workflow.add_node("build_queries", node_build_queries)
    workflow.add_node("multi_source_search", node_multi_source_search)
    workflow.add_node("conflict_resolve", node_conflict_resolve)
    workflow.add_node("inquiry_check", node_inquiry_check)
    workflow.add_node("generate_review", node_generate_review)

    # 入口: 信息脱敏
    workflow.set_entry_point("desensitize")

    # 脱敏 → 历史检查
    workflow.add_edge("desensitize", "check_history")

    # 历史检查路由
    workflow.add_conditional_edges(
        "check_history",
        route_history,
        {
            "parse_document": "parse_document",    # 完整审核
            "generate_review": "generate_review",  # 复用历史
        }
    )

    # 完整审核链路
    workflow.add_edge("parse_document", "struct_extract")
    workflow.add_edge("struct_extract", "build_queries")
    workflow.add_edge("build_queries", "multi_source_search")
    workflow.add_edge("multi_source_search", "conflict_resolve")
    workflow.add_edge("conflict_resolve", "inquiry_check")
    workflow.add_edge("inquiry_check", "generate_review")

    # 生成 → 结束
    workflow.add_edge("generate_review", END)

    return workflow.compile()
