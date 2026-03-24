"""工作流路由 + 集成测试"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestWorkflowRouting:
    """测试工作流路由函数"""

    def test_route_intent_chitchat(self):
        from graph.qa_workflow import route_intent
        state = {"intent": "chitchat"}
        assert route_intent(state) == "chitchat"

    def test_route_intent_knowledge(self):
        from graph.qa_workflow import route_intent
        state = {"intent": "knowledge_qa"}
        assert route_intent(state) == "query_process"

    def test_route_complexity_simple(self):
        from graph.qa_workflow import route_complexity
        state = {"deep_mode": False}
        assert route_complexity(state) == "simple_qa"

    def test_route_complexity_deep(self):
        from graph.qa_workflow import route_complexity
        state = {"deep_mode": True}
        assert route_complexity(state) == "deep_qa"

    def test_route_history_no_history(self):
        from graph.review_workflow import route_history
        state = {"has_history": False, "has_policy_change": True}
        assert route_history(state) == "parse_document"

    def test_route_history_with_change(self):
        from graph.review_workflow import route_history
        state = {"has_history": True, "has_policy_change": True}
        assert route_history(state) == "parse_document"

    def test_route_history_reuse(self):
        from graph.review_workflow import route_history
        state = {"has_history": True, "has_policy_change": False}
        assert route_history(state) == "generate_review"


@pytest.mark.integration
class TestQAWorkflowIntegration:
    """QA工作流集成测试(全部Agent Mock)"""

    def _make_state(self, query="测试问题"):
        from graph.qa_state import QAState
        return {
            "query": query,
            "session_id": "test-session",
            "desensitized_query": "",
            "pii_mapping": {},
            "intent": "",
            "deep_mode": False,
            "processed_queries": [],
            "query_type": "simple",
            "knowledge_results": [],
            "web_results": [],
            "resolved_context": "",
            "conflict_found": False,
            "conflict_summary": "",
            "history": [],
            "response": "",
            "steps": [],
        }

    @patch("graph.qa_nodes._get_desensitize_agent")
    @patch("graph.qa_nodes._get_intent_agent")
    @patch("graph.qa_nodes._get_response_agent")
    def test_chitchat_path(self, mock_resp, mock_intent, mock_desen):
        """寒暄路径：脱敏 → 意图(chitchat) → 直接生成"""
        from agents.desensitize_agent import DesensitizeAgent
        from agents.intent_agent import IntentAgent
        from agents.response_generator_agent import ResponseGeneratorAgent
        from conftest import MockLLMClient

        llm = MockLLMClient("你好呀！")

        desen = DesensitizeAgent(llm_client=llm)
        mock_desen.return_value = desen

        intent = IntentAgent(llm_client=MockLLMClient())
        intent._rule_based_classify = lambda q: {"intent": "chitchat", "deep_mode": False}
        intent.classify = lambda q, **kw: intent._rule_based_classify(q)
        mock_intent.return_value = intent

        resp = ResponseGeneratorAgent(llm_client=llm)
        mock_resp.return_value = resp

        from graph.qa_workflow import create_qa_workflow
        workflow = create_qa_workflow()
        state = self._make_state("你好")
        result = workflow.invoke(state)

        assert result["intent"] == "chitchat"
        assert len(result["steps"]) >= 2
        assert result["response"] != ""

    @patch("graph.qa_nodes._get_desensitize_agent")
    @patch("graph.qa_nodes._get_intent_agent")
    @patch("graph.qa_nodes._get_query_processor")
    @patch("graph.qa_nodes._get_knowledge_agent")
    @patch("graph.qa_nodes._get_response_agent")
    def test_simple_qa_path(self, mock_resp, mock_kb, mock_qp, mock_intent, mock_desen):
        """简单问答路径：脱敏 → 意图 → query处理 → 知识库 → 生成"""
        from agents.desensitize_agent import DesensitizeAgent
        from agents.intent_agent import IntentAgent
        from agents.query_processor_agent import QueryProcessorAgent
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        from agents.response_generator_agent import ResponseGeneratorAgent
        from conftest import MockLLMClient, MockDBManager

        llm = MockLLMClient("回答内容")

        mock_desen.return_value = DesensitizeAgent(llm_client=llm)

        intent = IntentAgent(llm_client=MockLLMClient())
        intent.classify = lambda q, **kw: {"intent": "knowledge_qa", "deep_mode": False}
        mock_intent.return_value = intent

        qp = QueryProcessorAgent(llm_client=MockLLMClient())
        qp.rewrite = lambda q: {"type": "simple", "queries": [q]}
        mock_qp.return_value = qp

        kb = KnowledgeExpertAgent(llm_client=llm, db_manager=MockDBManager([
            {"id": "1", "content": "知识内容", "metadata": {"source": "test.pdf"}},
        ]))
        mock_kb.return_value = kb

        mock_resp.return_value = ResponseGeneratorAgent(llm_client=llm)

        from graph.qa_workflow import create_qa_workflow
        workflow = create_qa_workflow()
        state = self._make_state("劳动法规定")
        result = workflow.invoke(state)

        assert result["intent"] == "knowledge_qa"
        assert result["deep_mode"] is False
        assert len(result["knowledge_results"]) >= 1
        assert result["response"] != ""
