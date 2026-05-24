"""
方案审核工作流节点函数

每个节点对应架构图3中的一个处理环节。
"""

import logging
import os
import time
from typing import Dict, Any
from .review_state import ReviewState

logger = logging.getLogger("review_workflow")

# ===== Agent延迟初始化 =====
_agents = {}

_ALL_AGENT_NAMES = [
    "desensitize", "history_review", "doc_parser", "struct_extract",
    "query_builder", "knowledge_expert", "web_search",
    "conflict_resolution", "inquiry", "plan_rewrite", "review_doc_generator",
]


def preload_all():
    """启动时预加载所有 Review Agent，避免首次请求延迟"""
    logger.info("[Review] 开始预加载所有 Agent...")
    for name in _ALL_AGENT_NAMES:
        _get_agent(name)
    logger.info("[Review] 所有 Agent 预加载完成")


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


def _log_text_chunks(label: str, text: str, chunk_size: int = 600, max_chunks: int = 8) -> None:
    """把长文本按段落输出为实时日志，避免一次性刷屏。"""
    if not text:
        logger.info("[Review]   %s：暂无内容", label)
        return
    total = len(text)
    chunks = [text[index:index + chunk_size] for index in range(0, total, chunk_size)]
    visible_chunks = chunks[:max_chunks]
    for index, chunk in enumerate(visible_chunks, 1):
        preview = chunk.replace("\r", " ").strip()
        logger.info("[Review]   %s片段 %d/%d | chars=%d | %s", label, index, len(chunks), len(chunk), preview[:220])
    if len(chunks) > max_chunks:
        logger.info("[Review]   %s剩余 %d 个片段已省略，完整内容将在文档预览/报告区展示", label, len(chunks) - max_chunks)


def _extract_risk_hints(doc_text: str) -> list:
    hints = []
    rules = [
        ("人员外包/派遣", ["外包", "派遣", "人力资源公司", "直接用工"], "核查是否涉及核心岗位人员分包或规避直接雇佣责任。"),
        ("劳动与社保", ["社保", "工会", "劳动合同", "劳动法"], "核查劳动合同、社保缴纳、工会沟通和雇主责任是否完整。"),
        ("利润分配", ["利润分配", "PTU", "Artículo 117", "117"], "核查墨西哥利润分配义务及新企业豁免条件是否被正确适用。"),
        ("第三方服务", ["设备维护", "废物处理", "物流运输", "专业服务"], "区分核心生产岗位与可外包的专业服务，保留供应商资质与合同边界。"),
    ]
    for title, keywords, suggestion in rules:
        if any(keyword in doc_text for keyword in keywords):
            hints.append({"title": title, "suggestion": suggestion})
    return hints or [{"title": "文档合规性", "suggestion": "围绕主体资质、合同边界、法律依据和执行留痕进行复核。"}]


def _fallback_rewrite_suggestions(state: ReviewState) -> str:
    doc_text = state.get("doc_text", "")
    hints = _extract_risk_hints(doc_text)
    lines = [
        "1. 将核心岗位、生产管理岗位与可外包的专业服务分开描述，避免把核心业务人员直接包装为外包服务。",
        "2. 对每一项外包安排补充法律依据、供应商资质、服务边界、验收标准和责任承担方式。",
        "3. 对涉及劳动合同、社保、工会沟通、利润分配等事项增加本地律师复核节点和证据留痕要求。",
    ]
    for index, hint in enumerate(hints, 4):
        lines.append(f"{index}. 针对“{hint['title']}”：{hint['suggestion']}")
    return "\n".join(lines)


def _fallback_review_report(state: ReviewState) -> str:
    doc_info = state.get("doc_info", {})
    doc_text = state.get("doc_text", "")
    hints = _extract_risk_hints(doc_text)
    risk_lines = "\n".join(
        f"- {hint['title']}：{hint['suggestion']}"
        for hint in hints
    )
    suggestions = state.get("rewrite_suggestions") or _fallback_rewrite_suggestions(state)
    return f"""## 1. 审核概要
已读取并解析文档《{doc_info.get('filename', '上传方案')}》，提取文本约 {len(doc_text)} 字。本报告基于当前文档内容生成，用于帮助用户进行初步合规判断。

## 2. 主要风险点
{risk_lines}

## 3. 修改建议
{suggestions}

## 4. 审核结论
该方案已经完成文档解析与流程化审核。由于当前模型/检索服务可能未返回完整外部依据，建议将以上风险点作为人工复核清单，并补充当地法律依据、合同条款和执行证据后再进入正式审批。"""


# ===== 节点函数 =====

def node_desensitize(state: ReviewState) -> Dict[str, Any]:
    """信息脱敏节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 信息脱敏 | query=%s", state["query"][:50])
    state["steps"].append("正在进行信息脱敏...")
    logger.info("[Review]   准备加载脱敏 Agent")
    agent = _get_agent("desensitize")
    logger.info("[Review]   开始扫描用户输入中的敏感信息")
    desensitized, mapping = agent.desensitize(state["query"])
    logger.info("[Review]   脱敏扫描完成，敏感项数量=%d", len(mapping))
    state["desensitized_query"] = desensitized
    state["pii_mapping"] = mapping
    if mapping:
        state["steps"].append(f"检测到 {len(mapping)} 个敏感信息已脱敏")
    logger.info("[Review] ✔ 信息脱敏完成 | pii=%d | %.2fs", len(mapping), time.time() - t0)
    return state


def node_check_history(state: ReviewState) -> Dict[str, Any]:
    """历史方案检查节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 历史方案检查")
    state["steps"].append("正在检查历史审核记录...")
    logger.info("[Review]   准备加载历史审核 Agent")
    agent = _get_agent("history_review")
    logger.info("[Review]   开始匹配历史审核记录与政策变更状态")
    result = agent.check_history(state.get("doc_info", {}))
    logger.info("[Review]   历史匹配结果：%s", result.get("recommendation", "执行完整审核"))
    state["has_history"] = result.get("has_history", False)
    state["has_policy_change"] = result.get("has_policy_change", True)
    state["steps"].append(f"历史检查完成: {result.get('recommendation', '执行完整审核')}")
    logger.info("[Review] ✔ 历史检查完成 | has_history=%s | %.2fs",
                state["has_history"], time.time() - t0)
    return state


def node_parse_document(state: ReviewState) -> Dict[str, Any]:
    """文档解析节点"""
    t0 = time.time()
    filepath = state["filepath"]
    logger.info("[Review] ▶ 文档解析 | filepath=%s", filepath)
    state["steps"].append("正在解析文档...")
    logger.info("[Review]   检查文件是否存在")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")
    ext = os.path.splitext(filepath)[1].lower()
    file_size = os.path.getsize(filepath)
    logger.info("[Review]   识别文件类型=%s，文件大小=%.1fKB", ext or "未知", file_size / 1024)
    logger.info("[Review]   准备加载文档解析 Agent")
    agent = _get_agent("doc_parser")
    logger.info("[Review]   开始提取文档文本内容")
    result = agent.parse(filepath)
    logger.info("[Review]   文本提取完成，开始整理文档元信息")
    _log_text_chunks("文档预览", result.get("text", ""), chunk_size=800, max_chunks=6)
    state["doc_info"] = {
        "filename": result["filename"],
        "file_type": result["file_type"],
        "char_count": result["char_count"],
    }
    state["doc_text"] = result["text"]
    state["steps"].append(
        f"文档解析完成: {result['filename']}, {result['char_count']} 字符"
    )
    logger.info("[Review] ✔ 文档解析完成 | chars=%d | %.2fs",
                result["char_count"], time.time() - t0)
    return state


def node_struct_extract(state: ReviewState) -> Dict[str, Any]:
    """结构化抽取节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 结构化抽取 | doc_len=%d", len(state["doc_text"]))
    state["steps"].append("正在提取文档结构化信息...")
    logger.info("[Review]   准备结构化抽取输入，截取文本长度=%d", len(state["doc_text"]))
    logger.info("[Review]   准备加载结构化抽取 Agent")
    agent = _get_agent("struct_extract")
    logger.info("[Review]   开始调用模型/规则抽取关键信息")
    result = agent.extract(state["doc_text"])
    state["structured_data"] = result.get("structured_data", {})
    logger.info("[Review]   已抽取字段数=%d", len(state["structured_data"]))
    for key, value in list(state["structured_data"].items())[:12]:
        logger.info("[Review]   字段：%s = %s", key, str(value)[:120])
    if result.get("success"):
        state["steps"].append("结构化信息提取完成")
    else:
        state["steps"].append(f"结构化抽取部分失败: {result.get('error', '')}")
    logger.info("[Review] ✔ 结构化抽取完成 | success=%s | %.2fs",
                result.get("success"), time.time() - t0)
    return state


def node_build_queries(state: ReviewState) -> Dict[str, Any]:
    """Query构造节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 构造审核查询")
    state["steps"].append("正在构造审核查询...")
    logger.info("[Review]   输入字段数=%d，用户审核需求长度=%d", len(state["structured_data"]), len(state["desensitized_query"]))
    logger.info("[Review]   准备加载 Query 构造 Agent")
    agent = _get_agent("query_builder")
    logger.info("[Review]   开始生成审核维度与检索 query")
    result = agent.build_queries(
        structured_data=state["structured_data"],
        user_query=state["desensitized_query"],
        doc_summary=state["doc_text"][:2000],
    )
    state["review_queries"] = result.get("queries", [])
    state["review_dimensions"] = result.get("dimensions", [])
    for index, query in enumerate(state["review_queries"], 1):
        logger.info("[Review]   Query %d/%d：%s", index, len(state["review_queries"]), query)
    for index, dimension in enumerate(state["review_dimensions"], 1):
        logger.info("[Review]   审核维度 %d/%d：%s", index, len(state["review_dimensions"]), dimension)
    state["steps"].append(
        f"已生成 {len(state['review_queries'])} 个审核查询, "
        f"维度: {', '.join(state['review_dimensions'])}"
    )
    logger.info("[Review] ✔ 查询构造完成 | queries=%d dims=%s | %.2fs",
                len(state["review_queries"]), state["review_dimensions"], time.time() - t0)
    return state


def node_multi_source_search(state: ReviewState) -> Dict[str, Any]:
    """多源检索节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 多源检索 | queries=%d", len(state["review_queries"]))
    state["steps"].append("正在进行多源检索(知识库+网络)...")

    logger.info("[Review]   准备加载知识库检索 Agent")
    kb_agent = _get_agent("knowledge_expert")
    logger.info("[Review]   准备加载网络检索 Agent")
    web_agent = _get_agent("web_search")

    kb_results = []
    web_results = []

    from core.config import settings
    web_enabled = settings.web_search_enabled
    if not web_enabled:
        logger.info("[Review] 网络检索已禁用(WEB_SEARCH_ENABLED=false)，仅检索知识库")

    total_queries = len(state["review_queries"])
    for index, query in enumerate(state["review_queries"], 1):
        logger.info("[Review]   Query %d/%d 开始检索：%s", index, total_queries, query)
        logger.info("[Review]     → 知识库检索中 top_k=3")
        kb_r = kb_agent.search(query, top_k=3)
        logger.info("[Review]     ← 知识库返回 %d 条", len(kb_r))
        for hit_index, item in enumerate(kb_r[:3], 1):
            source = item.get("metadata", {}).get("source") or item.get("source") or "知识库"
            preview = (item.get("content") or item.get("text") or item.get("excerpt") or "")[:120].replace("\n", " ")
            logger.info("[Review]       KB#%d [%s] %s", hit_index, str(source).split("/")[-1], preview)
        if web_enabled:
            logger.info("[Review]     → 网络检索中 max_results=3")
            web_r = web_agent.search(query, max_results=3)
            logger.info("[Review]     ← 网络返回 %d 条", len(web_r))
            for hit_index, item in enumerate(web_r[:3], 1):
                title = item.get("title") or item.get("source") or "网络结果"
                preview = (item.get("content") or item.get("snippet") or item.get("excerpt") or "")[:120].replace("\n", " ")
                logger.info("[Review]       WEB#%d [%s] %s", hit_index, title, preview)
        else:
            web_r = []
            logger.info("[Review]     跳过网络检索：WEB_SEARCH_ENABLED=false")
        kb_results.extend(kb_r)
        web_results.extend(web_r)
        logger.info("[Review]   Query %d/%d 检索完成：kb=%d web=%d", index, total_queries, len(kb_r), len(web_r))

    state["knowledge_results"] = kb_results
    state["web_results"] = web_results
    state["steps"].append(
        f"多源检索完成: 知识库 {len(kb_results)} 条, 网络 {len(web_results)} 条"
    )
    logger.info("[Review] ✔ 多源检索完成 | kb=%d web=%d | %.2fs",
                len(kb_results), len(web_results), time.time() - t0)
    return state


def node_conflict_resolve(state: ReviewState) -> Dict[str, Any]:
    """冲突裁决节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 冲突裁决 | kb=%d web=%d",
                len(state["knowledge_results"]), len(state["web_results"]))
    state["steps"].append("正在进行多源信息裁决...")
    logger.info("[Review]   汇总知识库结果 %d 条、网络结果 %d 条", len(state["knowledge_results"]), len(state["web_results"]))
    logger.info("[Review]   准备加载冲突裁决 Agent")
    agent = _get_agent("conflict_resolution")
    logger.info("[Review]   开始对多源结果进行一致性分析")
    result = agent.resolve(
        query=state["desensitized_query"],
        knowledge_results=state["knowledge_results"],
        web_results=state["web_results"],
    )
    state["resolved_context"] = result.get("resolved_context", "")
    state["conflict_found"] = result.get("conflict_found", False)
    state["conflict_summary"] = result.get("summary", "")
    logger.info("[Review]   冲突检测结果：conflict_found=%s", state["conflict_found"])
    logger.info("[Review]   裁决摘要：%s", state["conflict_summary"][:300])
    _log_text_chunks("裁决上下文", state["resolved_context"], chunk_size=700, max_chunks=4)
    state["steps"].append(f"裁决完成: {state['conflict_summary']}")
    logger.info("[Review] ✔ 冲突裁决完成 | conflict=%s | %.2fs",
                state["conflict_found"], time.time() - t0)
    return state


def node_inquiry_check(state: ReviewState) -> Dict[str, Any]:
    """质询自查节点"""
    t0 = time.time()
    logger.info("[Review] ▶ 审核自查")
    state["steps"].append("正在进行审核自查...")

    draft_parts = []
    if state.get("resolved_context"):
        draft_parts.append(state["resolved_context"])
    if state.get("conflict_summary"):
        draft_parts.append(f"冲突分析: {state['conflict_summary']}")
    draft = "\n\n".join(draft_parts) if draft_parts else "暂无审核草稿"

    logger.info("[Review]   生成自查草稿，长度=%d", len(draft))
    logger.info("[Review]   准备加载质询自查 Agent")
    agent = _get_agent("inquiry")
    logger.info("[Review]   开始进行审核质量自查")
    result = agent.self_check(
        review_draft=draft,
        original_doc_summary=state["doc_text"][:2000],
    )
    state["inquiry_result"] = result
    quality = result.get("quality_score", 0)
    logger.info("[Review]   自查质量评分：%s", quality)
    for index, issue in enumerate(result.get("issues", [])[:8], 1):
        logger.info("[Review]   自查问题 %d：[%s] %s", index, issue.get("type", "问题"), issue.get("description", ""))
    state["steps"].append(f"自查完成, 质量评分: {quality}")
    logger.info("[Review] ✔ 自查完成 | quality_score=%s | %.2fs", quality, time.time() - t0)
    return state


def node_generate_review(state: ReviewState) -> Dict[str, Any]:
    """审核文档生成节点"""
    t0 = time.time()
    kb_hits = state.get("knowledge_results", [])
    web_hits = state.get("web_results", [])
    context = state.get("resolved_context", "")

    logger.info("[Review] ▶ 生成审核报告 | kb命中=%d web命中=%d context_len=%d",
                len(kb_hits), len(web_hits), len(context))
    if kb_hits:
        logger.info("[Review]   知识库片段 TOP-%d:", len(kb_hits))
        for i, r in enumerate(kb_hits, 1):
            preview = r.get("content", "")[:100].replace("\n", " ")
            src = r.get("metadata", {}).get("source", "?").split("/")[-1]
            logger.info("[Review]     #%d [%s] %s…", i, src, preview)
    if web_hits:
        logger.info("[Review]   网络结果 TOP-%d:", min(len(web_hits), 3))
        for i, r in enumerate(web_hits[:3], 1):
            preview = r.get("content", "")[:80].replace("\n", " ")
            logger.info("[Review]     #%d %s…", i, preview)
    if state.get("conflict_summary"):
        logger.info("[Review]   冲突裁决摘要: %s", state["conflict_summary"][:120])

    state["steps"].append("正在生成审核报告...")

    logger.info("[Review]   阶段 1/2：生成方案优化建议")
    logger.info("[Review]   准备加载方案优化 Agent")
    rewrite_agent = _get_agent("plan_rewrite")
    logger.info("[Review]   调用模型生成方案优化建议，输入原文摘要长度=%d，审核发现长度=%d", len(state["doc_text"][:3000]), len(state.get("resolved_context", "")))
    rewrite_result = rewrite_agent.rewrite(
        original_text=state["doc_text"][:3000],
        review_findings=state.get("resolved_context", ""),
    )
    state["rewrite_suggestions"] = rewrite_result.get("suggestions", "")
    if not rewrite_result.get("success") or not state["rewrite_suggestions"].strip():
        logger.info("[Review]   方案优化模型结果为空，启用基于文档内容的兜底优化建议")
        state["rewrite_suggestions"] = _fallback_rewrite_suggestions(state)
    logger.info("[Review]   方案优化建议生成完成，长度=%d，success=%s", len(state["rewrite_suggestions"]), rewrite_result.get("success"))
    _log_text_chunks("优化建议", state["rewrite_suggestions"], chunk_size=500, max_chunks=8)

    logger.info("[Review]   阶段 2/2：生成正式审核报告")
    logger.info("[Review]   准备加载审核报告生成 Agent")
    generator = _get_agent("review_doc_generator")
    logger.info("[Review]   调用模型生成审核报告")
    result = generator.generate(
        doc_info=state["doc_info"],
        structured_data=state["structured_data"],
        resolved_context=state["resolved_context"],
        conflict_summary=state["conflict_summary"],
        inquiry_result=state.get("inquiry_result", {}),
        rewrite_suggestions=state["rewrite_suggestions"],
    )

    review_report = result.get("review_report", "审核报告生成失败")
    if (
        not result.get("success")
        or not review_report.strip()
        or "审核报告生成失败" in review_report
    ):
        logger.info("[Review]   审核报告模型结果不可用，启用基于文档内容的兜底审核报告")
        review_report = _fallback_review_report(state)
    logger.info("[Review]   审核报告模型输出完成，长度=%d，success=%s", len(review_report), result.get("success"))
    _log_text_chunks("审核报告", review_report, chunk_size=700, max_chunks=10)

    mapping = state.get("pii_mapping", {})
    if mapping:
        logger.info("[Review]   检测到脱敏映射，开始还原报告中的敏感占位符")
        from agents.desensitize_agent import DesensitizeAgent
        review_report = DesensitizeAgent.restore(review_report, mapping)
        logger.info("[Review]   敏感占位符还原完成")

    state["review_report"] = review_report
    state["response"] = review_report
    state["steps"].append("审核报告生成完成")
    logger.info("[Review] ✔ 审核报告生成完成 | report_len=%d | %.2fs",
                len(review_report), time.time() - t0)
    return state
