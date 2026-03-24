"""
方案审核工作流状态定义

对应架构图3的完整流程：
信息脱敏 → 意图识别 → 历史检查 → 文档解析 → 结构化抽取
→ Query构造 → 多源检索 → 冲突裁决 → 质询自查 → 审核文档生成
"""

from typing import TypedDict, List, Optional, Dict, Any


class ReviewState(TypedDict):
    # 用户输入
    query: str                              # 用户审核需求描述
    session_id: str                         # 会话ID
    filepath: str                           # 上传文件路径

    # 脱敏
    desensitized_query: str
    pii_mapping: Dict[str, str]

    # 意图识别
    intent: str

    # 历史检查
    has_history: bool
    has_policy_change: bool

    # 文档解析
    doc_info: Dict[str, Any]                # 文件元信息
    doc_text: str                           # 解析后的文本

    # 结构化抽取
    structured_data: Dict[str, Any]         # 结构化字段

    # Query构造
    review_queries: List[str]               # 审核查询列表
    review_dimensions: List[str]            # 审核维度

    # 多源检索
    knowledge_results: List[Dict[str, Any]]
    web_results: List[Dict[str, Any]]

    # 冲突裁决
    resolved_context: str
    conflict_found: bool
    conflict_summary: str

    # 质询自查
    inquiry_result: Dict[str, Any]

    # 方案重写建议
    rewrite_suggestions: str

    # 最终输出
    review_report: str                      # 审核报告
    response: str                           # 给用户的回复

    # 流程跟踪
    steps: List[str]
