"""QA节点函数单元测试 + 深度问答路径集成测试"""

import pytest
from unittest.mock import patch, MagicMock
from conftest import MockLLMClient, MockLLMJsonClient, MockLLMFailClient, MockDBManager, MockSearchClient


@pytest.mark.unit
class TestQANodeDesensitize:
    """脱敏节点测试"""

    @patch("graph.qa_nodes._get_desensitize_agent")
    def test_no_pii(self, mock_get, qa_state_factory):
        from agents.desensitize_agent import DesensitizeAgent
        mock_get.return_value = DesensitizeAgent()

        from graph.qa_nodes import node_desensitize
        state = qa_state_factory(query="今天天气怎么样")
        result = node_desensitize(state)
        assert result["desensitized_query"] == "今天天气怎么样"
        assert result["pii_mapping"] == {}
        assert "未检测到敏感信息" in result["steps"][-1]

    @patch("graph.qa_nodes._get_desensitize_agent")
    def test_with_pii(self, mock_get, qa_state_factory):
        from agents.desensitize_agent import DesensitizeAgent
        mock_get.return_value = DesensitizeAgent()

        from graph.qa_nodes import node_desensitize
        state = qa_state_factory(query="电话13812345678的合同")
        result = node_desensitize(state)
        assert "13812345678" not in result["desensitized_query"]
        assert len(result["pii_mapping"]) == 1
        assert "敏感信息已脱敏" in result["steps"][-1]


@pytest.mark.unit
class TestQANodeIntentRecognize:
    """意图识别节点测试"""

    @patch("graph.qa_nodes._get_intent_agent")
    def test_chitchat(self, mock_get, qa_state_factory):
        from agents.intent_agent import IntentAgent
        agent = IntentAgent(llm_client=MockLLMFailClient())
        mock_get.return_value = agent

        from graph.qa_nodes import node_intent_recognize
        state = qa_state_factory(desensitized_query="你好")
        result = node_intent_recognize(state)
        assert result["intent"] == "chitchat"
        assert result["deep_mode"] is False

    @patch("graph.qa_nodes._get_intent_agent")
    def test_deep_mode(self, mock_get, qa_state_factory):
        from agents.intent_agent import IntentAgent
        agent = IntentAgent(llm_client=MockLLMFailClient())
        mock_get.return_value = agent

        from graph.qa_nodes import node_intent_recognize
        state = qa_state_factory(desensitized_query="详细分析法律条款")
        result = node_intent_recognize(state)
        assert result["intent"] == "knowledge_qa"
        assert result["deep_mode"] is True


@pytest.mark.unit
class TestQANodeQueryProcess:
    """Query处理节点测试"""

    @patch("graph.qa_nodes._get_query_processor")
    def test_simple_rewrite(self, mock_get, qa_state_factory):
        from agents.query_processor_agent import QueryProcessorAgent
        agent = QueryProcessorAgent(llm_client=MockLLMFailClient())
        mock_get.return_value = agent

        from graph.qa_nodes import node_query_process
        state = qa_state_factory(desensitized_query="劳动法", deep_mode=False)
        result = node_query_process(state)
        assert result["query_type"] == "simple"
        assert len(result["processed_queries"]) >= 1

    @patch("graph.qa_nodes._get_query_processor")
    def test_complex_decompose(self, mock_get, qa_state_factory):
        from agents.query_processor_agent import QueryProcessorAgent
        agent = QueryProcessorAgent(llm_client=MockLLMFailClient())
        mock_get.return_value = agent

        from graph.qa_nodes import node_query_process
        state = qa_state_factory(desensitized_query="复杂问题", deep_mode=True)
        result = node_query_process(state)
        assert result["query_type"] == "complex"


@pytest.mark.unit
class TestQANodeSimpleQA:
    """简单问答节点测试"""

    @patch("graph.qa_nodes._get_knowledge_agent")
    def test_with_results(self, mock_get, qa_state_factory):
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        db = MockDBManager([
            {"id": "1", "content": "法律条文内容", "metadata": {"source": "law.pdf"}},
        ])
        mock_get.return_value = KnowledgeExpertAgent(llm_client=MockLLMClient(), db_manager=db)

        from graph.qa_nodes import node_simple_qa
        state = qa_state_factory(processed_queries=["劳动法"])
        result = node_simple_qa(state)
        assert len(result["knowledge_results"]) == 1
        assert result["conflict_found"] is False
        assert "法律条文" in result["resolved_context"]

    @patch("graph.qa_nodes._get_knowledge_agent")
    def test_empty_results(self, mock_get, qa_state_factory):
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        mock_get.return_value = KnowledgeExpertAgent(
            llm_client=MockLLMClient(), db_manager=MockDBManager([])
        )

        from graph.qa_nodes import node_simple_qa
        state = qa_state_factory(processed_queries=["不存在的内容"])
        result = node_simple_qa(state)
        assert len(result["knowledge_results"]) == 0
        assert result["resolved_context"] == ""


@pytest.mark.unit
class TestQANodeDeepQA:
    """深度问答节点测试"""

    @patch("graph.qa_nodes._get_web_search_agent")
    @patch("graph.qa_nodes._get_knowledge_agent")
    def test_both_sources(self, mock_kb, mock_web, qa_state_factory):
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        from agents.web_search_agent import WebSearchAgent

        mock_kb.return_value = KnowledgeExpertAgent(
            llm_client=MockLLMClient(),
            db_manager=MockDBManager([{"id": "1", "content": "知识库", "metadata": {}}]),
        )
        mock_web.return_value = WebSearchAgent(
            llm_client=MockLLMClient(),
            search_client=MockSearchClient([
                {"title": "网络", "url": "https://x.com", "content": "网络内容"},
            ]),
        )

        from graph.qa_nodes import node_deep_qa
        state = qa_state_factory(processed_queries=["q1"])
        result = node_deep_qa(state)
        assert len(result["knowledge_results"]) >= 1
        assert len(result["web_results"]) >= 1
        assert "多源检索完成" in result["steps"][-1]


@pytest.mark.unit
class TestQANodeConflictResolve:
    """冲突裁决节点测试"""

    @patch("graph.qa_nodes._get_conflict_agent")
    def test_no_results(self, mock_get, qa_state_factory):
        from agents.conflict_resolution_agent import ConflictResolutionAgent
        mock_get.return_value = ConflictResolutionAgent(llm_client=MockLLMClient())

        from graph.qa_nodes import node_conflict_resolve
        state = qa_state_factory(
            desensitized_query="测试",
            knowledge_results=[],
            web_results=[],
        )
        result = node_conflict_resolve(state)
        assert result["conflict_found"] is False
        assert "未找到" in result["conflict_summary"]

    @patch("graph.qa_nodes._get_conflict_agent")
    def test_only_knowledge(self, mock_get, qa_state_factory):
        from agents.conflict_resolution_agent import ConflictResolutionAgent
        mock_get.return_value = ConflictResolutionAgent(llm_client=MockLLMClient())

        from graph.qa_nodes import node_conflict_resolve
        state = qa_state_factory(
            desensitized_query="测试",
            knowledge_results=[{"content": "知识内容"}],
            web_results=[],
        )
        result = node_conflict_resolve(state)
        assert result["conflict_found"] is False
        assert "知识库" in result["conflict_summary"]


@pytest.mark.unit
class TestQANodeGenerateResponse:
    """回复生成节点测试"""

    @patch("graph.qa_nodes._get_response_agent")
    def test_generate(self, mock_get, qa_state_factory):
        from agents.response_generator_agent import ResponseGeneratorAgent
        mock_get.return_value = ResponseGeneratorAgent(llm_client=MockLLMClient("最终回复"))

        from graph.qa_nodes import node_generate_response
        state = qa_state_factory(
            desensitized_query="测试问题",
            intent="knowledge_qa",
            resolved_context="上下文",
        )
        result = node_generate_response(state)
        assert result["response"] == "最终回复"
        assert "回复生成完成" in result["steps"][-1]

    @patch("graph.qa_nodes._get_response_agent")
    def test_pii_restore(self, mock_get, qa_state_factory):
        """测试回复中PII被还原"""
        from agents.response_generator_agent import ResponseGeneratorAgent
        mock_get.return_value = ResponseGeneratorAgent(
            llm_client=MockLLMClient("联系 [PHONE_0] 获取详情")
        )

        from graph.qa_nodes import node_generate_response
        state = qa_state_factory(
            desensitized_query="测试",
            intent="knowledge_qa",
            pii_mapping={"[PHONE_0]": "13812345678"},
        )
        result = node_generate_response(state)
        assert "13812345678" in result["response"]
        assert "[PHONE_0]" not in result["response"]


# ===== 深度问答完整路径集成测试 =====

@pytest.mark.integration
class TestQADeepPathIntegration:
    """深度问答路径端到端: 脱敏→意图→query处理→深度QA→冲突裁决→生成"""

    @patch("graph.qa_nodes._get_desensitize_agent")
    @patch("graph.qa_nodes._get_intent_agent")
    @patch("graph.qa_nodes._get_query_processor")
    @patch("graph.qa_nodes._get_knowledge_agent")
    @patch("graph.qa_nodes._get_web_search_agent")
    @patch("graph.qa_nodes._get_conflict_agent")
    @patch("graph.qa_nodes._get_response_agent")
    def test_deep_qa_full_path(
        self, mock_resp, mock_conflict, mock_web, mock_kb,
        mock_qp, mock_intent, mock_desen, qa_state_factory
    ):
        from agents.desensitize_agent import DesensitizeAgent
        from agents.intent_agent import IntentAgent
        from agents.query_processor_agent import QueryProcessorAgent
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        from agents.web_search_agent import WebSearchAgent
        from agents.conflict_resolution_agent import ConflictResolutionAgent
        from agents.response_generator_agent import ResponseGeneratorAgent

        llm = MockLLMClient("深度回复内容")

        mock_desen.return_value = DesensitizeAgent(llm_client=llm)

        intent = IntentAgent(llm_client=MockLLMFailClient())
        intent.classify = lambda q, **kw: {"intent": "knowledge_qa", "deep_mode": True}
        mock_intent.return_value = intent

        qp = QueryProcessorAgent(llm_client=MockLLMFailClient())
        qp.decompose = lambda q: {"type": "complex", "queries": ["子问题1", "子问题2"]}
        mock_qp.return_value = qp

        mock_kb.return_value = KnowledgeExpertAgent(
            llm_client=llm,
            db_manager=MockDBManager([
                {"id": "1", "content": "知识内容A", "metadata": {"source": "a.pdf"}},
            ]),
        )
        mock_web.return_value = WebSearchAgent(
            llm_client=llm,
            search_client=MockSearchClient([
                {"title": "网络A", "url": "https://x.com", "content": "网络内容A"},
            ]),
        )

        conflict = ConflictResolutionAgent(llm_client=MockLLMFailClient())
        mock_conflict.return_value = conflict

        mock_resp.return_value = ResponseGeneratorAgent(llm_client=llm)

        from graph.qa_workflow import create_qa_workflow
        workflow = create_qa_workflow()
        state = qa_state_factory(query="详细分析墨西哥劳动法的加班规定")
        result = workflow.invoke(state)

        assert result["intent"] == "knowledge_qa"
        assert result["deep_mode"] is True
        assert result["query_type"] == "complex"
        assert len(result["processed_queries"]) == 2
        assert len(result["knowledge_results"]) >= 1
        assert len(result["web_results"]) >= 1
        assert result["response"] != ""
        assert len(result["steps"]) >= 5  # 至少5个步骤

    @patch("graph.qa_nodes._get_desensitize_agent")
    @patch("graph.qa_nodes._get_intent_agent")
    @patch("graph.qa_nodes._get_query_processor")
    @patch("graph.qa_nodes._get_knowledge_agent")
    @patch("graph.qa_nodes._get_web_search_agent")
    @patch("graph.qa_nodes._get_conflict_agent")
    @patch("graph.qa_nodes._get_response_agent")
    def test_deep_qa_with_pii_roundtrip(
        self, mock_resp, mock_conflict, mock_web, mock_kb,
        mock_qp, mock_intent, mock_desen, qa_state_factory
    ):
        """深度问答+PII全流程: 输入有PII → 脱敏 → 处理 → 回复中还原PII"""
        from agents.desensitize_agent import DesensitizeAgent
        from agents.intent_agent import IntentAgent
        from agents.query_processor_agent import QueryProcessorAgent
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        from agents.web_search_agent import WebSearchAgent
        from agents.conflict_resolution_agent import ConflictResolutionAgent
        from agents.response_generator_agent import ResponseGeneratorAgent

        mock_desen.return_value = DesensitizeAgent()

        intent = IntentAgent(llm_client=MockLLMFailClient())
        intent.classify = lambda q, **kw: {"intent": "knowledge_qa", "deep_mode": True}
        mock_intent.return_value = intent

        qp = QueryProcessorAgent(llm_client=MockLLMFailClient())
        qp.decompose = lambda q: {"type": "complex", "queries": [q]}
        mock_qp.return_value = qp

        mock_kb.return_value = KnowledgeExpertAgent(
            llm_client=MockLLMClient(),
            db_manager=MockDBManager([]),
        )
        mock_web.return_value = WebSearchAgent(
            llm_client=MockLLMClient(),
            search_client=MockSearchClient([]),
        )
        mock_conflict.return_value = ConflictResolutionAgent(llm_client=MockLLMClient())

        # 回复中包含脱敏占位符, 应在最终输出中被还原
        mock_resp.return_value = ResponseGeneratorAgent(
            llm_client=MockLLMClient("请联系 [PHONE_0] 了解详情")
        )

        from graph.qa_workflow import create_qa_workflow
        workflow = create_qa_workflow()
        state = qa_state_factory(query="查询13812345678的合同")
        result = workflow.invoke(state)

        # PII在脱敏阶段被替换
        assert "13812345678" not in result["desensitized_query"]
        # 最终回复中被还原
        assert "13812345678" in result["response"]
