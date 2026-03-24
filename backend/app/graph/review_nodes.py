"""
方案审核工作流节点函数

每个节点对应架构图3中的一个处理环节。
"""

from typing import Dict, Any
from .review_state import ReviewState

# ===== Agent延迟初始化 =====
_agents = {}


def _get_agent(name: str):
    if name not in _agents:
        if name == "desensitize":
            from agents.desensitize_agent import DesensitizeAgent
            _agents[name] = DesensitizeAgent()
        elif name == "history_review":
            from agents.history_review_agent import HistoryReviewAgent
            _agents[name] = HistoryReviewAgent()
        elif name == "doc_parser":
            from agents.doc_parser_agent import DocParserAgent
            _agents[name] = DocParserAgent()
        elif name == "struct_extract":
            from agents.struct_extract_agent import StructExtractAgent
            _agents[name] = StructExtractAgent()
        elif name == "query_builder":
            from agents.query_builder_agent import QueryBuilderAgent
            _agents[name] = QueryBuilderAgent()
        elif name == "knowledge_expert":
            from agents.knowledge_expert_agent import KnowledgeExpertAgent
            _agents[name] = KnowledgeExpertAgent()
        elif name == "web_search":
            from agents.web_search_agent import WebSearchAgent
            _agents[name] = WebSearchAgent()
        elif name == "conflict_resolution":
            from agents.conflict_resolution_agent import ConflictResolutionAgent
            _agents[name] = ConflictResolutionAgent()
        elif name == "inquiry":
            from agents.inquiry_agent import InquiryAgent
            _agents[name] = InquiryAgent()
        elif name == "plan_rewrite":
            from agents.plan_rewrite_agent import PlanRewriteAgent
            _agents[name] = PlanRewriteAgent()
        elif name == "review_doc_generator":
            from agents.review_doc_generator_agent import ReviewDocGeneratorAgent
            _agents[name] = ReviewDocGeneratorAgent()
    return _agents[name]


# ===== 节点函数 =====

def node_desensitize(state: ReviewState) -> Dict[str, Any]:
    """信息脱敏节点"""
    state["steps"].append("正在进行信息脱敏...")
    agent = _get_agent("desensitize")
    desensitized, mapping = agent.desensitize(state["query"])
    state["desensitized_query"] = desensitized
    state["pii_mapping"] = mapping
    if mapping:
        state["steps"].append(f"检测到 {len(mapping)} 个敏感信息已脱敏")
    return state


def node_check_history(state: ReviewState) -> Dict[str, Any]:
    """历史方案检查节点"""
    state["steps"].append("正在检查历史审核记录...")
    agent = _get_agent("history_review")
    result = agent.check_history(state.get("doc_info", {}))
    state["has_history"] = result.get("has_history", False)
    state["has_policy_change"] = result.get("has_policy_change", True)
    state["steps"].append(f"历史检查完成: {result.get('recommendation', '执行完整审核')}")
    return state


def node_parse_document(state: ReviewState) -> Dict[str, Any]:
    """文档解析节点"""
    state["steps"].append("正在解析文档...")
    agent = _get_agent("doc_parser")
    result = agent.parse(state["filepath"])
    state["doc_info"] = {
        "filename": result["filename"],
        "file_type": result["file_type"],
        "char_count": result["char_count"],
    }
    state["doc_text"] = result["text"]
    state["steps"].append(
        f"文档解析完成: {result['filename']}, {result['char_count']} 字符"
    )
    return state


def node_struct_extract(state: ReviewState) -> Dict[str, Any]:
    """结构化抽取节点"""
    state["steps"].append("正在提取文档结构化信息...")
    agent = _get_agent("struct_extract")
    result = agent.extract(state["doc_text"])
    state["structured_data"] = result.get("structured_data", {})
    if result.get("success"):
        state["steps"].append("结构化信息提取完成")
    else:
        state["steps"].append(f"结构化抽取部分失败: {result.get('error', '')}")
    return state


def node_build_queries(state: ReviewState) -> Dict[str, Any]:
    """Query构造节点"""
    state["steps"].append("正在构造审核查询...")
    agent = _get_agent("query_builder")
    result = agent.build_queries(
        structured_data=state["structured_data"],
        user_query=state["desensitized_query"],
        doc_summary=state["doc_text"][:2000],
    )
    state["review_queries"] = result.get("queries", [])
    state["review_dimensions"] = result.get("dimensions", [])
    state["steps"].append(
        f"已生成 {len(state['review_queries'])} 个审核查询, "
        f"维度: {', '.join(state['review_dimensions'])}"
    )
    return state


def node_multi_source_search(state: ReviewState) -> Dict[str, Any]:
    """多源检索节点"""
    state["steps"].append("正在进行多源检索(知识库+网络)...")

    kb_agent = _get_agent("knowledge_expert")
    web_agent = _get_agent("web_search")

    kb_results = []
    web_results = []

    for query in state["review_queries"]:
        kb_results.extend(kb_agent.search(query, top_k=3))
        web_results.extend(web_agent.search(query, max_results=3))

    state["knowledge_results"] = kb_results
    state["web_results"] = web_results
    state["steps"].append(
        f"多源检索完成: 知识库 {len(kb_results)} 条, 网络 {len(web_results)} 条"
    )
    return state


def node_conflict_resolve(state: ReviewState) -> Dict[str, Any]:
    """冲突裁决节点"""
    state["steps"].append("正在进行多源信息裁决...")
    agent = _get_agent("conflict_resolution")
    result = agent.resolve(
        query=state["desensitized_query"],
        knowledge_results=state["knowledge_results"],
        web_results=state["web_results"],
    )
    state["resolved_context"] = result.get("resolved_context", "")
    state["conflict_found"] = result.get("conflict_found", False)
    state["conflict_summary"] = result.get("summary", "")
    state["steps"].append(f"裁决完成: {state['conflict_summary']}")
    return state


def node_inquiry_check(state: ReviewState) -> Dict[str, Any]:
    """质询自查节点"""
    state["steps"].append("正在进行审核自查...")

    # 先用已有结果构建初步审核草稿
    draft_parts = []
    if state.get("resolved_context"):
        draft_parts.append(state["resolved_context"])
    if state.get("conflict_summary"):
        draft_parts.append(f"冲突分析: {state['conflict_summary']}")
    draft = "\n\n".join(draft_parts) if draft_parts else "暂无审核草稿"

    agent = _get_agent("inquiry")
    result = agent.self_check(
        review_draft=draft,
        original_doc_summary=state["doc_text"][:2000],
    )
    state["inquiry_result"] = result
    quality = result.get("quality_score", 0)
    state["steps"].append(f"自查完成, 质量评分: {quality}")
    return state


def node_generate_review(state: ReviewState) -> Dict[str, Any]:
    """审核文档生成节点"""
    state["steps"].append("正在生成审核报告...")

    # 尝试生成修改建议
    rewrite_agent = _get_agent("plan_rewrite")
    rewrite_result = rewrite_agent.rewrite(
        original_text=state["doc_text"][:3000],
        review_findings=state.get("resolved_context", ""),
    )
    state["rewrite_suggestions"] = rewrite_result.get("suggestions", "")

    # 生成完整审核报告
    generator = _get_agent("review_doc_generator")
    result = generator.generate(
        doc_info=state["doc_info"],
        structured_data=state["structured_data"],
        resolved_context=state["resolved_context"],
        conflict_summary=state["conflict_summary"],
        inquiry_result=state.get("inquiry_result", {}),
        rewrite_suggestions=state["rewrite_suggestions"],
    )

    review_report = result.get("review_report", "审核报告生成失败")

    # 还原脱敏信息
    mapping = state.get("pii_mapping", {})
    if mapping:
        from agents.desensitize_agent import DesensitizeAgent
        review_report = DesensitizeAgent.restore(review_report, mapping)

    state["review_report"] = review_report
    state["response"] = review_report
    state["steps"].append("审核报告生成完成")
    return state
