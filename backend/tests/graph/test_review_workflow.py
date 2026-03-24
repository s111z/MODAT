"""审核工作流节点 + 集成测试"""

import pytest
from unittest.mock import patch
from conftest import (
    MockLLMClient, MockLLMJsonClient, MockLLMFailClient,
    MockDBManager, MockSearchClient,
)


@pytest.mark.unit
class TestReviewNodeDesensitize:

    @patch("graph.review_nodes._get_agent")
    def test_desensitize(self, mock_get, review_state_factory):
        from agents.desensitize_agent import DesensitizeAgent
        mock_get.return_value = DesensitizeAgent()

        from graph.review_nodes import node_desensitize
        state = review_state_factory(query="电话13812345678审核")
        result = node_desensitize(state)
        assert "13812345678" not in result["desensitized_query"]
        assert len(result["pii_mapping"]) == 1


@pytest.mark.unit
class TestReviewNodeCheckHistory:

    @patch("graph.review_nodes._get_agent")
    def test_no_history(self, mock_get, review_state_factory):
        from agents.history_review_agent import HistoryReviewAgent
        mock_get.return_value = HistoryReviewAgent()

        from graph.review_nodes import node_check_history
        state = review_state_factory()
        result = node_check_history(state)
        assert result["has_history"] is False
        assert result["has_policy_change"] is True


@pytest.mark.unit
class TestReviewNodeParseDocument:

    @patch("graph.review_nodes._get_agent")
    def test_parse_txt(self, mock_get, review_state_factory, sample_txt_path):
        from agents.doc_parser_agent import DocParserAgent
        mock_get.return_value = DocParserAgent()

        from graph.review_nodes import node_parse_document
        state = review_state_factory(filepath=sample_txt_path)
        result = node_parse_document(state)
        assert result["doc_text"] != ""
        assert result["doc_info"]["file_type"] == ".txt"
        assert result["doc_info"]["char_count"] > 0
        assert "文档解析完成" in result["steps"][-1]


@pytest.mark.unit
class TestReviewNodeStructExtract:

    @patch("graph.review_nodes._get_agent")
    def test_extract(self, mock_get, review_state_factory):
        from agents.struct_extract_agent import StructExtractAgent
        llm = MockLLMJsonClient({"company_name": "测试公司", "location": "墨西哥"})
        mock_get.return_value = StructExtractAgent(llm_client=llm)

        from graph.review_nodes import node_struct_extract
        state = review_state_factory(doc_text="测试文档内容关于测试公司在墨西哥的方案")
        result = node_struct_extract(state)
        assert result["structured_data"]["company_name"] == "测试公司"
        assert "结构化信息提取完成" in result["steps"][-1]

    @patch("graph.review_nodes._get_agent")
    def test_extract_fail(self, mock_get, review_state_factory):
        from agents.struct_extract_agent import StructExtractAgent
        mock_get.return_value = StructExtractAgent(llm_client=MockLLMFailClient())

        from graph.review_nodes import node_struct_extract
        state = review_state_factory(doc_text="内容")
        result = node_struct_extract(state)
        assert "失败" in result["steps"][-1]


@pytest.mark.unit
class TestReviewNodeBuildQueries:

    @patch("graph.review_nodes._get_agent")
    def test_build(self, mock_get, review_state_factory):
        from agents.query_builder_agent import QueryBuilderAgent
        llm = MockLLMJsonClient({
            "queries": ["合规性检查", "风险分析"],
            "dimensions": ["法规", "风险"],
        })
        mock_get.return_value = QueryBuilderAgent(llm_client=llm)

        from graph.review_nodes import node_build_queries
        state = review_state_factory(
            structured_data={"location": "墨西哥"},
            desensitized_query="审核请求",
            doc_text="文档内容",
        )
        result = node_build_queries(state)
        assert len(result["review_queries"]) == 2
        assert len(result["review_dimensions"]) == 2


@pytest.mark.unit
class TestReviewNodeMultiSourceSearch:

    @patch("graph.review_nodes._get_agent")
    def test_search(self, mock_get, review_state_factory):
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        from agents.web_search_agent import WebSearchAgent

        kb = KnowledgeExpertAgent(
            llm_client=MockLLMClient(),
            db_manager=MockDBManager([{"id": "1", "content": "知识", "metadata": {}}]),
        )
        web = WebSearchAgent(
            llm_client=MockLLMClient(),
            search_client=MockSearchClient([
                {"title": "网络", "url": "https://x.com", "content": "网络内容"},
            ]),
        )

        def side_effect(name):
            if name == "knowledge_expert":
                return kb
            if name == "web_search":
                return web
            raise ValueError(f"Unknown: {name}")

        mock_get.side_effect = side_effect

        from graph.review_nodes import node_multi_source_search
        state = review_state_factory(review_queries=["q1", "q2"])
        result = node_multi_source_search(state)
        assert len(result["knowledge_results"]) >= 1
        assert len(result["web_results"]) >= 1
        assert "多源检索完成" in result["steps"][-1]


@pytest.mark.unit
class TestReviewNodeGenerateReview:

    @patch("graph.review_nodes._get_agent")
    def test_generate(self, mock_get, review_state_factory):
        from agents.plan_rewrite_agent import PlanRewriteAgent
        from agents.review_doc_generator_agent import ReviewDocGeneratorAgent

        rewrite = PlanRewriteAgent(llm_client=MockLLMClient("修改建议"))
        generator = ReviewDocGeneratorAgent(llm_client=MockLLMClient("## 审核报告\n审核通过"))

        def side_effect(name):
            if name == "plan_rewrite":
                return rewrite
            if name == "review_doc_generator":
                return generator
            raise ValueError(f"Unknown: {name}")

        mock_get.side_effect = side_effect

        from graph.review_nodes import node_generate_review
        state = review_state_factory(
            doc_info={"filename": "test.txt", "file_type": ".txt", "char_count": 100},
            doc_text="文档内容",
            structured_data={"company_name": "公司"},
            resolved_context="上下文",
            conflict_summary="无冲突",
        )
        result = node_generate_review(state)
        assert "审核报告" in result["review_report"]
        assert result["response"] == result["review_report"]
        assert "审核报告生成完成" in result["steps"][-1]


# ===== 审核工作流端到端集成测试 =====

@pytest.mark.integration
class TestReviewWorkflowIntegration:

    @patch("graph.review_nodes._get_agent")
    def test_full_review_path(self, mock_get, review_state_factory, sample_txt_path):
        """完整审核路径: 脱敏→历史→解析→抽取→query→检索→裁决→自查→生成"""
        from agents.desensitize_agent import DesensitizeAgent
        from agents.history_review_agent import HistoryReviewAgent
        from agents.doc_parser_agent import DocParserAgent
        from agents.struct_extract_agent import StructExtractAgent
        from agents.query_builder_agent import QueryBuilderAgent
        from agents.knowledge_expert_agent import KnowledgeExpertAgent
        from agents.web_search_agent import WebSearchAgent
        from agents.conflict_resolution_agent import ConflictResolutionAgent
        from agents.inquiry_agent import InquiryAgent
        from agents.plan_rewrite_agent import PlanRewriteAgent
        from agents.review_doc_generator_agent import ReviewDocGeneratorAgent

        llm = MockLLMClient("生成内容")
        llm_json_struct = MockLLMJsonClient({"company_name": "测试公司"})
        llm_json_query = MockLLMJsonClient({
            "queries": ["合规检查"], "dimensions": ["法规"]
        })
        llm_json_inquiry = MockLLMJsonClient({
            "issues_found": False, "issues": [], "quality_score": 90, "summary": "OK"
        })

        agents_map = {
            "desensitize": DesensitizeAgent(),
            "history_review": HistoryReviewAgent(),
            "doc_parser": DocParserAgent(),
            "struct_extract": StructExtractAgent(llm_client=llm_json_struct),
            "query_builder": QueryBuilderAgent(llm_client=llm_json_query),
            "knowledge_expert": KnowledgeExpertAgent(
                llm_client=llm, db_manager=MockDBManager([])
            ),
            "web_search": WebSearchAgent(
                llm_client=llm, search_client=MockSearchClient([])
            ),
            "conflict_resolution": ConflictResolutionAgent(llm_client=llm),
            "inquiry": InquiryAgent(llm_client=llm_json_inquiry),
            "plan_rewrite": PlanRewriteAgent(llm_client=llm),
            "review_doc_generator": ReviewDocGeneratorAgent(llm_client=llm),
        }

        # 清除全局agent缓存
        import graph.review_nodes as rn
        rn._agents.clear()
        mock_get.side_effect = lambda name: agents_map[name]

        from graph.review_workflow import create_review_workflow
        workflow = create_review_workflow()
        state = review_state_factory(filepath=sample_txt_path)
        result = workflow.invoke(state)

        # 验证完整路径
        assert result["has_policy_change"] is True
        assert result["doc_text"] != ""
        assert result["doc_info"]["file_type"] == ".txt"
        assert len(result["review_queries"]) >= 1
        assert result["response"] != ""
        assert len(result["steps"]) >= 8  # 至少8个步骤
