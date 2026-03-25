"""
知识问答工作流节点函数

每个节点函数接收QAState，调用对应Agent，更新并返回state。
"""

import logging
import time
from typing import Dict, Any
from .qa_state import QAState

logger = logging.getLogger("qa_workflow")


# ===== Agent实例(延迟初始化) =====
_desensitize_agent = None
_intent_agent = None
_query_processor = None
_knowledge_agent = None
_web_search_agent = None
_conflict_agent = None
_response_agent = None


def preload_all():
    """启动时预加载所有 QA Agent，避免首次请求延迟"""
    logger.info("[QA] 开始预加载所有 Agent...")
    _get_desensitize_agent()
    _get_intent_agent()
    _get_query_processor()
    _get_knowledge_agent()
    _get_web_search_agent()
    _get_conflict_agent()
    _get_response_agent()
    logger.info("[QA] 所有 Agent 预加载完成")


def _get_desensitize_agent():
    global _desensitize_agent
    if _desensitize_agent is None:
        from agents.desensitize_agent import DesensitizeAgent
        _desensitize_agent = DesensitizeAgent()
    return _desensitize_agent


def _get_intent_agent():
    global _intent_agent
    if _intent_agent is None:
        from agents.intent_agent import IntentAgent
        _intent_agent = IntentAgent()
    return _intent_agent


def _get_query_processor():
    global _query_processor
    if _query_processor is None:
        from agents.query_processor_agent import QueryProcessorAgent
        _query_processor = QueryProcessorAgent()
    return _query_processor


def _get_knowledge_agent():
    global _knowledge_agent
    if _knowledge_agent is None:
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        _knowledge_agent = KnowledgeExpertAgent()
    return _knowledge_agent


def _get_web_search_agent():
    global _web_search_agent
    if _web_search_agent is None:
        from agents.web_search_agent import WebSearchAgent
        _web_search_agent = WebSearchAgent()
    return _web_search_agent


def _get_conflict_agent():
    global _conflict_agent
    if _conflict_agent is None:
        from agents.conflict_resolution_agent import ConflictResolutionAgent
        _conflict_agent = ConflictResolutionAgent()
    return _conflict_agent


def _get_response_agent():
    global _response_agent
    if _response_agent is None:
        from agents.response_generator_agent import ResponseGeneratorAgent
        _response_agent = ResponseGeneratorAgent()
    return _response_agent


# ===== 节点函数 =====

def node_desensitize(state: QAState) -> Dict[str, Any]:
    """信息脱敏节点"""
    t0 = time.time()
    logger.info("[QA] ▶ 信息脱敏 | query=%s", state["query"][:50])
    state["steps"].append("正在进行信息脱敏...")

    agent = _get_desensitize_agent()
    desensitized, mapping = agent.desensitize(state["query"])

    state["desensitized_query"] = desensitized
    state["pii_mapping"] = mapping

    if mapping:
        state["steps"].append(f"检测到 {len(mapping)} 个敏感信息已脱敏")
    else:
        state["steps"].append("未检测到敏感信息")
    logger.info("[QA] ✔ 信息脱敏完成 | pii=%d | %.2fs", len(mapping), time.time() - t0)
    return state


def node_intent_recognize(state: QAState) -> Dict[str, Any]:
    """意图识别节点"""
    t0 = time.time()
    logger.info("[QA] ▶ 意图识别 | query=%s", state["desensitized_query"][:50])
    state["steps"].append("正在识别用户意图...")

    agent = _get_intent_agent()
    result = agent.classify(state["desensitized_query"])

    state["intent"] = result.get("intent", "knowledge_qa")
    state["deep_mode"] = result.get("deep_mode", False)

    mode_text = "深度思考" if state["deep_mode"] else "快速回答"
    state["steps"].append(f"意图: {state['intent']}, 模式: {mode_text}")
    logger.info("[QA] ✔ 意图识别完成 | intent=%s deep_mode=%s | %.2fs",
                state["intent"], state["deep_mode"], time.time() - t0)
    return state


def node_query_process(state: QAState) -> Dict[str, Any]:
    """Query处理节点"""
    t0 = time.time()
    logger.info("[QA] ▶ Query处理 | deep_mode=%s", state["deep_mode"])
    state["steps"].append("正在处理查询...")

    agent = _get_query_processor()

    if state["deep_mode"]:
        result = agent.decompose(state["desensitized_query"])
    else:
        result = agent.rewrite(state["desensitized_query"])

    state["processed_queries"] = result.get("queries", [state["desensitized_query"]])
    state["query_type"] = result.get("type", "simple")

    state["steps"].append(
        f"Query处理完成: {state['query_type']}, "
        f"共{len(state['processed_queries'])}个查询"
    )
    logger.info("[QA] ✔ Query处理完成 | type=%s queries=%d | %.2fs",
                state["query_type"], len(state["processed_queries"]), time.time() - t0)
    return state


def node_simple_qa(state: QAState) -> Dict[str, Any]:
    """简单问答节点 - 仅查询知识库"""
    t0 = time.time()
    logger.info("[QA] ▶ 知识库检索 | queries=%d", len(state["processed_queries"]))
    state["steps"].append("正在检索知识库...")

    agent = _get_knowledge_agent()
    all_results = []
    for query in state["processed_queries"]:
        results = agent.search(query, top_k=3)
        all_results.extend(results)
        logger.debug("[QA]   检索 '%s' → %d 条", query[:30], len(results))

    state["knowledge_results"] = all_results
    state["resolved_context"] = agent.format_context(all_results)
    state["conflict_found"] = False

    state["steps"].append(f"知识库检索完成，找到 {len(all_results)} 条结果")
    logger.info("[QA] ✔ 知识库检索完成 | hits=%d | %.2fs", len(all_results), time.time() - t0)
    return state


def node_deep_qa(state: QAState) -> Dict[str, Any]:
    """深度问答节点 - 并行查询知识库+网络"""
    t0 = time.time()
    logger.info("[QA] ▶ 深度检索(知识库+网络) | queries=%d", len(state["processed_queries"]))
    state["steps"].append("正在并行检索知识库和网络...")

    kb_agent = _get_knowledge_agent()
    web_agent = _get_web_search_agent()

    kb_results = []
    web_results = []

    for query in state["processed_queries"]:
        results = kb_agent.search(query, top_k=3)
        kb_results.extend(results)
        logger.debug("[QA]   KB '%s' → %d 条", query[:30], len(results))

    for query in state["processed_queries"]:
        results = web_agent.search(query, max_results=3)
        web_results.extend(results)
        logger.debug("[QA]   Web '%s' → %d 条", query[:30], len(results))

    state["knowledge_results"] = kb_results
    state["web_results"] = web_results

    state["steps"].append(
        f"多源检索完成: 知识库 {len(kb_results)} 条, 网络 {len(web_results)} 条"
    )
    logger.info("[QA] ✔ 深度检索完成 | kb=%d web=%d | %.2fs",
                len(kb_results), len(web_results), time.time() - t0)
    return state


def node_conflict_resolve(state: QAState) -> Dict[str, Any]:
    """冲突裁决节点"""
    t0 = time.time()
    logger.info("[QA] ▶ 冲突裁决 | kb=%d web=%d",
                len(state["knowledge_results"]), len(state.get("web_results", [])))
    state["steps"].append("正在进行多源信息裁决...")

    agent = _get_conflict_agent()
    result = agent.resolve(
        query=state["desensitized_query"],
        knowledge_results=state["knowledge_results"],
        web_results=state.get("web_results", []),
    )

    state["resolved_context"] = result.get("resolved_context", "")
    state["conflict_found"] = result.get("conflict_found", False)
    state["conflict_summary"] = result.get("summary", "")

    if state["conflict_found"]:
        state["steps"].append(f"发现信息冲突，已完成裁决: {state['conflict_summary']}")
    else:
        state["steps"].append(f"多源信息一致: {state['conflict_summary']}")

    logger.info("[QA] ✔ 冲突裁决完成 | conflict=%s | %.2fs",
                state["conflict_found"], time.time() - t0)
    return state


def node_generate_response(state: QAState) -> Dict[str, Any]:
    """回复生成节点"""
    t0 = time.time()
    context = state.get("resolved_context", "")
    kb_hits = state.get("knowledge_results", [])
    web_hits = state.get("web_results", [])

    logger.info("[QA] ▶ 回复生成 | kb命中=%d web命中=%d context_len=%d",
                len(kb_hits), len(web_hits), len(context))
    if kb_hits:
        logger.info("[QA]   知识库片段 TOP-%d:", len(kb_hits))
        for i, r in enumerate(kb_hits, 1):
            preview = r.get("content", "")[:100].replace("\n", " ")
            src = r.get("metadata", {}).get("source", "?").split("/")[-1]
            logger.info("[QA]     #%d [%s] %s…", i, src, preview)
    if web_hits:
        logger.info("[QA]   网络结果 TOP-%d:", min(len(web_hits), 3))
        for i, r in enumerate(web_hits[:3], 1):
            preview = r.get("content", "")[:80].replace("\n", " ")
            logger.info("[QA]     #%d %s…", i, preview)
    if not kb_hits and not web_hits:
        logger.warning("[QA]   ⚠ 无任何检索结果，将仅凭 LLM 知识生成回复")

    state["steps"].append("正在生成回复...")

    agent = _get_response_agent()
    result = agent.generate(
        query=state["desensitized_query"],
        context=state.get("resolved_context", ""),
        intent=state["intent"],
        history=state.get("history", []),
    )

    response = result.get("response", "抱歉，未能生成回复")

    # 还原脱敏信息
    mapping = state.get("pii_mapping", {})
    if mapping:
        from agents.desensitize_agent import DesensitizeAgent
        response = DesensitizeAgent.restore(response, mapping)

    state["response"] = response
    state["steps"].append("回复生成完成")
    logger.info("[QA] ✔ 回复生成完成 | response_len=%d | %.2fs", len(response), time.time() - t0)
    return state
