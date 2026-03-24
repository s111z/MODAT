"""DocParserAgent + 审核Agent 单元测试"""

import pytest
import os
import tempfile
from agents.doc_parser_agent import DocParserAgent


@pytest.mark.unit
class TestDocParserAgent:

    def test_parse_txt(self, sample_txt_path):
        agent = DocParserAgent()
        result = agent.parse(sample_txt_path)
        assert result["file_type"] == ".txt"
        assert result["char_count"] > 0
        assert "测试文档" in result["text"]

    def test_parse_pdf(self, sample_pdf_path):
        if sample_pdf_path is None:
            pytest.skip("测试PDF文件不存在")
        agent = DocParserAgent()
        result = agent.parse(sample_pdf_path)
        assert result["file_type"] == ".pdf"
        assert result["char_count"] > 0

    def test_file_not_found(self):
        agent = DocParserAgent()
        with pytest.raises(FileNotFoundError):
            agent.parse("/not/exist/file.pdf")

    def test_unsupported_type(self, tmp_path):
        xlsx = tmp_path / "test.xlsx"
        xlsx.write_bytes(b"fake")
        agent = DocParserAgent()
        with pytest.raises(ValueError, match="不支持"):
            agent.parse(str(xlsx))


@pytest.mark.unit
class TestStructExtractAgent:

    def test_extract_success(self, mock_llm_json):
        from agents.struct_extract_agent import StructExtractAgent
        mock_llm_json.json_data = {"company_name": "测试公司", "location": "墨西哥"}
        agent = StructExtractAgent(llm_client=mock_llm_json)
        result = agent.extract("测试文档内容")
        assert result["success"] is True
        assert result["structured_data"]["company_name"] == "测试公司"

    def test_extract_llm_fail(self, mock_llm_fail):
        from agents.struct_extract_agent import StructExtractAgent
        agent = StructExtractAgent(llm_client=mock_llm_fail)
        result = agent.extract("测试文档内容")
        assert result["success"] is False


@pytest.mark.unit
class TestQueryBuilderAgent:

    def test_build_queries_success(self, mock_llm_json):
        from agents.query_builder_agent import QueryBuilderAgent
        mock_llm_json.json_data = {
            "queries": ["法规合规性", "财务合理性"],
            "dimensions": ["法规", "财务"],
        }
        agent = QueryBuilderAgent(llm_client=mock_llm_json)
        result = agent.build_queries({"location": "墨西哥"})
        assert len(result["queries"]) == 2

    def test_fallback_queries(self, mock_llm_fail):
        from agents.query_builder_agent import QueryBuilderAgent
        agent = QueryBuilderAgent(llm_client=mock_llm_fail)
        result = agent.build_queries(
            {"key_regulations": "劳动法", "location": "墨西哥"},
            user_query="审核合规性",
        )
        assert len(result["queries"]) >= 1
        assert len(result["dimensions"]) >= 1


@pytest.mark.unit
class TestInquiryAgent:

    def test_self_check_success(self, mock_llm_json):
        from agents.inquiry_agent import InquiryAgent
        mock_llm_json.json_data = {
            "issues_found": False,
            "issues": [],
            "quality_score": 85,
            "summary": "质量良好",
        }
        agent = InquiryAgent(llm_client=mock_llm_json)
        result = agent.self_check("审核草稿内容")
        assert result["quality_score"] == 85

    def test_self_check_fail(self, mock_llm_fail):
        from agents.inquiry_agent import InquiryAgent
        agent = InquiryAgent(llm_client=mock_llm_fail)
        result = agent.self_check("草稿")
        assert result["quality_score"] == 0


@pytest.mark.unit
class TestPlanRewriteAgent:

    def test_rewrite_success(self, mock_llm):
        from agents.plan_rewrite_agent import PlanRewriteAgent
        mock_llm.response = "1. 修改建议一\n2. 修改建议二"
        agent = PlanRewriteAgent(llm_client=mock_llm)
        result = agent.rewrite("原始方案", "审核发现问题")
        assert result["success"] is True
        assert "修改建议" in result["suggestions"]


@pytest.mark.unit
class TestReviewDocGeneratorAgent:

    def test_generate_success(self, mock_llm):
        from agents.review_doc_generator_agent import ReviewDocGeneratorAgent
        mock_llm.response = "## 1. 审核概要\n审核报告内容..."
        agent = ReviewDocGeneratorAgent(llm_client=mock_llm)
        result = agent.generate(
            doc_info={"filename": "test.pdf", "file_type": ".pdf", "char_count": 1000},
            structured_data={"company_name": "测试公司"},
            resolved_context="检索结果上下文",
        )
        assert result["success"] is True
        assert "审核" in result["review_report"]
