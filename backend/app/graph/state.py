from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    messages: List[str]  # 对话消息历史
    files: List[str]  # 文件路径列表
    documents: List[str]  # 上传的文档内容
    review_status: Optional[str]  # 文档评审状态
    steps: List[str]  # 代理执行步骤(用于UI展示)
    current_mode: Optional[str]  # 当前模式: "review"或"qa"
    web_results: List[str]  # 网络搜索结果
    rag_results: List[str]  # RAG搜索结果
    ruling_results: List[str]  # 冲突分析步骤
    query: str  # 用户原始查询

"""
{
    "title": "",
    "url": "",
    "content": "",
    "source": "duckduckgo"
}
"""                                     