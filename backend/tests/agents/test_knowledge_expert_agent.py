"""KnowledgeExpertAgent单元测试"""

import pytest
from agents.knowledge_expert_agent import KnowledgeExpertAgent


@pytest.mark.unit
class TestKnowledgeExpertAgent:

    def test_search_normal(self, mock_llm, mock_db_manager):
        agent = KnowledgeExpertAgent(llm_client=mock_llm, db_manager=mock_db_manager)
        results = agent.search("测试查询", top_k=2)
        assert len(results) == 2
        assert mock_db_manager.call_count == 1

    def test_search_empty(self, mock_llm, mock_db_empty):
        agent = KnowledgeExpertAgent(llm_client=mock_llm, db_manager=mock_db_empty)
        results = agent.search("不存在的内容")
        assert results == []

    def test_search_exception(self, mock_llm):
        db = mock_db_manager = type("FailDB", (), {"search": lambda *a, **kw: (_ for _ in ()).throw(Exception("DB error"))})()
        agent = KnowledgeExpertAgent(llm_client=mock_llm, db_manager=db)
        results = agent.search("测试")
        assert results == []

    def test_format_context_normal(self, mock_llm, mock_db_manager):
        agent = KnowledgeExpertAgent(llm_client=mock_llm, db_manager=mock_db_manager)
        results = mock_db_manager.results
        text = agent.format_context(results)
        assert "来源1" in text
        assert "测试文档内容1" in text

    def test_format_context_empty(self, mock_llm, mock_db_manager):
        agent = KnowledgeExpertAgent(llm_client=mock_llm, db_manager=mock_db_manager)
        text = agent.format_context([])
        assert text == ""

    def test_execute_multi_query(self, mock_llm, mock_db_manager):
        import asyncio
        agent = KnowledgeExpertAgent(llm_client=mock_llm, db_manager=mock_db_manager)
        result = asyncio.get_event_loop().run_until_complete(
            agent.execute({"queries": ["q1", "q2"], "top_k": 2})
        )
        assert result["source"] == "knowledge_base"
        assert len(result["searches"]) == 2
