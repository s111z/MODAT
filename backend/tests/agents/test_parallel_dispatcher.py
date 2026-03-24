"""ParallelDispatcher单元测试"""

import pytest
import asyncio
from agents.parallel_dispatcher import ParallelDispatcher
from agents.knowledge_expert_agent import KnowledgeExpertAgent
from agents.web_search_agent import WebSearchAgent


@pytest.mark.unit
class TestParallelDispatcher:

    def _make_dispatcher(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = ParallelDispatcher(llm_client=mock_llm)
        dispatcher.knowledge_agent = KnowledgeExpertAgent(
            llm_client=mock_llm, db_manager=mock_db_manager
        )
        dispatcher.web_search_agent = WebSearchAgent(
            llm_client=mock_llm, search_client=mock_search_client
        )
        return dispatcher

    def test_dispatch_both_sources(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = self._make_dispatcher(mock_llm, mock_db_manager, mock_search_client)
        result = asyncio.get_event_loop().run_until_complete(
            dispatcher.dispatch(["测试查询"], ["knowledge", "web"], top_k=2)
        )
        assert "knowledge" in result
        assert "web" in result
        assert result["knowledge"]["source"] == "knowledge_base"
        assert result["web"]["source"] == "web_search"

    def test_dispatch_knowledge_only(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = self._make_dispatcher(mock_llm, mock_db_manager, mock_search_client)
        result = asyncio.get_event_loop().run_until_complete(
            dispatcher.dispatch(["测试"], ["knowledge"], top_k=2)
        )
        assert "knowledge" in result
        assert "web" not in result

    def test_dispatch_web_only(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = self._make_dispatcher(mock_llm, mock_db_manager, mock_search_client)
        result = asyncio.get_event_loop().run_until_complete(
            dispatcher.dispatch(["测试"], ["web"], top_k=2)
        )
        assert "web" in result
        assert "knowledge" not in result

    def test_dispatch_multi_query(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = self._make_dispatcher(mock_llm, mock_db_manager, mock_search_client)
        result = asyncio.get_event_loop().run_until_complete(
            dispatcher.dispatch(["q1", "q2", "q3"], ["knowledge", "web"])
        )
        # 每个source应该有3组搜索结果
        assert len(result["knowledge"]["searches"]) == 3
        assert len(result["web"]["searches"]) == 3

    def test_collect_all_results(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = self._make_dispatcher(mock_llm, mock_db_manager, mock_search_client)
        dispatch_output = {
            "knowledge": {
                "source": "knowledge_base",
                "searches": [
                    {"query": "q1", "results": [{"content": "kb1"}], "count": 1},
                    {"query": "q2", "results": [{"content": "kb2"}], "count": 1},
                ]
            },
            "web": {
                "source": "web_search",
                "searches": [
                    {"query": "q1", "results": [{"content": "web1"}], "count": 1},
                ]
            }
        }
        kb_results, web_results = dispatcher.collect_all_results(dispatch_output)
        assert len(kb_results) == 2
        assert len(web_results) == 1

    def test_collect_all_results_empty(self, mock_llm, mock_db_manager, mock_search_client):
        dispatcher = self._make_dispatcher(mock_llm, mock_db_manager, mock_search_client)
        kb, web = dispatcher.collect_all_results({})
        assert kb == []
        assert web == []

    def test_dispatch_handles_exception(self, mock_llm, mock_db_fail, mock_search_client):
        """知识库异常时应降级返回error而不是崩溃"""
        dispatcher = self._make_dispatcher(mock_llm, mock_db_fail, mock_search_client)
        # knowledge agent 内部会捕获异常返回空列表，不会抛到dispatch层
        result = asyncio.get_event_loop().run_until_complete(
            dispatcher.dispatch(["测试"], ["knowledge", "web"])
        )
        assert "knowledge" in result
        assert "web" in result
