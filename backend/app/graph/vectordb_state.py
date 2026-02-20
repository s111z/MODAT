from typing import TypedDict, List, Optional, Dict, Any

# 新增文件入库要先进行上传，然后再执行操作
class VectorDBState(TypedDict):
    """向量库工作流状态

    用于管理向量库 CRUD 操作的状态信息
    单个文档的操作状态
    """
    operation: str  # 操作类型: "add", "search", "update", "delete", "get_all"
    filename: str # 要操作的文件
    content: str # 文件内容列表
    
    # 文档元数据
    file_id: str # 文件标识符
    source: str # 文档来源
    file_type: str # 文件类型，后缀 
    chunk_index: int # chunk索引，数字
    total_chunks: int # 总chunk数
    created_at: str # 创建时间
    category: str # 文档类别，用内容划分
    permissions: int # 文档权限，用数字分级

    # 查询
    query: Optional[str]  # 搜索查询字符串
    top_k: Optional[int]  # 搜索返回的结果数量
    filter_meta: Optional[Dict]  # 过滤条件，用于搜索或删除
    
    # 操作数据
    results: List[Dict[str, Any]]  # 操作结果列表
    success: bool  # 操作是否成功
    message: str  # 操作结果消息
    steps: List[str]  # 执行步骤列表（用于日志和UI展示）
    answer: Optional[str]