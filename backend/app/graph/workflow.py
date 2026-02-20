from typing import Literal
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    node_parse_doc,
    node_search_web,
    node_rag_search,
    node_conflict_resolution,
    node_generate_response
)

def route_question(state: AgentState) -> Literal["simple", "deep"]:
    """路由决策：判断使用简单RAG还是深度研究模式"""
    # 简单判断逻辑：如果有文档上传，使用深度研究模式
    if state.get("documents"):
        return "deep"
    
    # 如果消息包含特定关键词，使用深度研究模式
    messages = state.get("messages", [])
    if messages:
        last_message = messages[-1].lower() if messages else ""
        if any(keyword in last_message for keyword in ["详细", "深入", "分析", "研究"]):
            return "deep"
    
    return "simple"

def create_workflow() -> StateGraph:
    """创建并返回完整的工作流图"""
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("parse_doc", node_parse_doc)
    workflow.add_node("search_web", node_search_web)
    workflow.add_node("rag_search", node_rag_search)
    workflow.add_node("conflict_resolution", node_conflict_resolution)
    workflow.add_node("generate_response", node_generate_response)
    
    # 设置入口点 - 根据模式路由
    workflow.set_conditional_entry_point(
        route_question,
        {
            "simple": "rag_search",
            "deep": "parse_doc"
        }
    )
    
    # 简单模式路径：RAG搜索 -> 生成响应 -> 结束
    workflow.add_edge("rag_search", "generate_response")
    
    # 深度模式路径：解析文档 -> (网络搜索 | RAG搜索) -> 冲突解决 -> 生成响应 -> 结束
    workflow.add_edge("parse_doc", "search_web")
    workflow.add_edge("parse_doc", "rag_search")
    # workflow.add_edge("search_web", "rag_search")
    
    # 从RAG搜索到冲突解决的条件边
    def should_resolve_conflict(state: AgentState) -> Literal["conflict_resolution", "generate_response"]:
        """判断是否需要冲突解决"""
        if state.get("web_results") and state.get("rag_results"):
            return "conflict_resolution"
        return "generate_response"
    
    # 设置冲突解决点
    workflow.add_conditional_edges(
        "rag_search",
        should_resolve_conflict,
        {
            "conflict_resolution": "conflict_resolution",
            "generate_response": "generate_response"
        }
    )
    
    workflow.add_edge("conflict_resolution", "generate_response")
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()