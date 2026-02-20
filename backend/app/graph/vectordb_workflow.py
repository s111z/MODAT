from typing import Literal
from langgraph.graph import StateGraph, END
from .vectordb_state import VectorDBState
from .vectordb_nodes import (
    node_add_documents,
    node_search_documents,
    node_update_document,
    node_delete_documents,
    node_get_all_documents,
    node_generate_response
)

def route_operation(state: VectorDBState) -> Literal["add", "search", "update", "delete", "get_all"]:
    """根据操作类型路由到不同节点
    
    Args:
        state: 向量库工作流状态
        
    Returns:
        操作类型字符串，对应不同的节点名称
    """
    operation = state.get("operation", "search")
    
    if operation == "add":
        return "add"
    elif operation == "update":
        return "update"
    elif operation == "delete":
        return "delete"
    elif operation == "get_all":
        return "get_all"
    else:
        return "search"

def after_search_routing(state: VectorDBState) -> Literal["generate", "end"]:
    """搜索之后的路由
    根据搜索结果是否匹配来决定是否生成回答
    """
    if state.get("operation") == "qa":
        return "generate"
    else:
        return "end"

def create_vectordb_workflow() -> StateGraph:
    """创建向量库管理工作流
    
    构建一个基于 LangGraph 的状态图，支持向量库的增删改查操作
    
    Returns:
        编译后的工作流图
    """
    workflow = StateGraph(VectorDBState)
    
    # 添加所有节点
    workflow.add_node("add", node_add_documents)
    workflow.add_node("search", node_search_documents)
    workflow.add_node("generate_response", node_generate_response)
    workflow.add_node("update", node_update_document)
    workflow.add_node("delete", node_delete_documents)
    workflow.add_node("get_all", node_get_all_documents)
    # workflow.add_node("parse_doc", node_parse_doc)
    
    # 设置条件入口点，根据操作类型路由
    workflow.set_conditional_entry_point(
        route_operation,
        {
            "add": "add",
            "search": "search",
            "update": "update",
            "delete": "delete",
            "get_all": "get_all"
        }
    )
    
    # 所有节点执行后直接结束
    workflow.add_edge("add",END)
    
    workflow.add_conditional_edges(
        "search",                 # 从 search 节点出发
        after_search_routing,     # 调用上面写的判断函数
        {
            "generate": "generate", # 如果函数返回 "generate"，则跳转到 generate 节点
            "end": END              # 如果函数返回 "end"，则流程直接结束
        }
    )

    workflow.add_edge("update", END)
    workflow.add_edge("delete", END)
    workflow.add_edge("get_all", END)
    
    return workflow.compile()