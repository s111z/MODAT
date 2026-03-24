"""
知识问答工作流状态定义

对应架构图2的完整流程：
信息脱敏 → 意图识别 → Query处理 → 知识收集 → 冲突裁决 → 回复生成
"""

from typing import TypedDict, List, Optional, Dict, Any


class QAState(TypedDict):
    # 用户输入
    query: str                              # 原始用户查询
    session_id: str                         # 会话ID

    # 脱敏
    desensitized_query: str                 # 脱敏后的查询
    pii_mapping: Dict[str, str]             # PII映射表

    # 意图识别
    intent: str                             # 意图: knowledge_qa / chitchat
    deep_mode: bool                         # 是否深度思考模式

    # Query处理
    processed_queries: List[str]            # 处理后的query列表
    query_type: str                         # simple / complex

    # 知识收集
    knowledge_results: List[Dict[str, Any]] # 知识库检索结果
    web_results: List[Dict[str, Any]]       # 网络搜索结果

    # 冲突裁决
    resolved_context: str                   # 裁决后的上下文
    conflict_found: bool                    # 是否发现冲突
    conflict_summary: str                   # 裁决概要

    # 对话历史
    history: List[Dict[str, str]]           # 多轮对话历史

    # 生成
    response: str                           # 最终回复

    # 流程跟踪
    steps: List[str]                        # Agent执行步骤
