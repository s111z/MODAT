"""
知识问答工作流

对应架构图2：
信息脱敏 → 意图识别 → Query处理 → 知识收集 → 冲突裁决 → 回复生成

支持三种路径：
1. 寒暄 → 直接回复
2. 简单问答 → 知识库检索 → 回复
3. 深度问答 → 并行检索 → 冲突裁决 → 回复
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from .qa_state import QAState
from .qa_nodes import (
    node_desensitize,
    node_intent_recognize,
    node_query_process,
    node_simple_qa,
    node_deep_qa,
    node_conflict_resolve,
    node_generate_response,
)


def route_intent(state: QAState) -> Literal["chitchat", "query_process"]:
    """意图路由：寒暄直接生成，其余进入query处理"""
    if state.get("intent") == "chitchat":
        return "chitchat"
    return "query_process"


def route_complexity(state: QAState) -> Literal["simple_qa", "deep_qa"]:
    """复杂度路由：简单问答 or 深度问答"""
    if state.get("deep_mode", False):
        return "deep_qa"
    return "simple_qa"


def create_qa_workflow():
    """创建知识问答工作流"""
    workflow = StateGraph(QAState)

    # 添加节点
    workflow.add_node("desensitize", node_desensitize)
    workflow.add_node("intent_recognize", node_intent_recognize)
    workflow.add_node("query_process", node_query_process)
    workflow.add_node("simple_qa", node_simple_qa)
    workflow.add_node("deep_qa", node_deep_qa)
    workflow.add_node("conflict_resolve", node_conflict_resolve)
    workflow.add_node("generate_response", node_generate_response)

    # 入口: 信息脱敏
    workflow.set_entry_point("desensitize")

    # 脱敏 → 意图识别
    workflow.add_edge("desensitize", "intent_recognize")

    # 意图路由
    workflow.add_conditional_edges(
        "intent_recognize",
        route_intent,
        {
            "chitchat": "generate_response",   # 寒暄 → 直接生成
            "query_process": "query_process",  # 知识问答 → query处理
        }
    )

    # query处理后路由
    workflow.add_conditional_edges(
        "query_process",
        route_complexity,
        {
            "simple_qa": "simple_qa",  # 简单 → 知识库检索
            "deep_qa": "deep_qa",      # 深度 → 并行检索
        }
    )

    # 简单问答 → 直接生成
    workflow.add_edge("simple_qa", "generate_response")

    # 深度问答 → 冲突裁决 → 生成
    workflow.add_edge("deep_qa", "conflict_resolve")
    workflow.add_edge("conflict_resolve", "generate_response")

    # 生成 → 结束
    workflow.add_edge("generate_response", END)

    return workflow.compile()
