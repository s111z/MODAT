import pytest
from unittest.mock import MagicMock, patch, mock_open
from app.core.parse_doc import extract_text_from_pdf


class TestExtractTextFromPDF:
    """测试extract_text_from_pdf函数"""

    def test_non_pdf_file_raises_error(self):
        """测试非PDF文件抛出异常"""
        with pytest.raises(ValueError, match="非 PDF 文件"):
            extract_text_from_pdf("document.txt")

        with pytest.raises(ValueError, match="非 PDF 文件"):
            extract_text_from_pdf("image.jpg")

        with pytest.raises(ValueError, match="非 PDF 文件"):
            extract_text_from_pdf("data.json")

    @patch("app.core.parse_doc.fitz.open")
    def test_extract_text_from_single_page(self, mock_fitz_open):
        """测试从单页PDF提取文本"""
        # 模拟页面对象
        mock_page = MagicMock()
        mock_page.get_text.return_value = "这是第一页的文本内容"

        # 模拟文档对象
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]

        mock_fitz_open.return_value = mock_doc

        result = extract_text_from_pdf("test.pdf")

        assert result == "这是第一页的文本内容"
        mock_fitz_open.assert_called_once_with("test.pdf")
        mock_page.get_text.assert_called_once()

    @patch("app.core.parse_doc.fitz.open")
    def test_extract_text_from_multiple_pages(self, mock_fitz_open):
        """测试从多页PDF提取文本"""
        # 模拟多个页面
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "第一页内容"

        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "第二页内容"

        mock_page3 = MagicMock()
        mock_page3.get_text.return_value = "第三页内容"

        # 模拟文档对象
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page1, mock_page2, mock_page3]

        mock_fitz_open.return_value = mock_doc

        result = extract_text_from_pdf("multi_page.pdf")

        assert result == "第一页内容第二页内容第三页内容"
        mock_fitz_open.assert_called_once_with("multi_page.pdf")
        assert mock_page1.get_text.call_count == 1
        assert mock_page2.get_text.call_count == 1
        assert mock_page3.get_text.call_count == 1

    @patch("app.core.parse_doc.fitz.open")
    def test_extract_text_from_empty_pdf(self, mock_fitz_open):
        """测试从空PDF提取文本"""
        # 模拟空文档
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = []

        mock_fitz_open.return_value = mock_doc

        result = extract_text_from_pdf("empty.pdf")

        assert result == ""
        mock_fitz_open.assert_called_once_with("empty.pdf")

    @patch("app.core.parse_doc.fitz.open")
    def test_extract_text_with_whitespace(self, mock_fitz_open):
        """测试提取包含空白字符的文本"""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "   文本前有空格   \n换行符也会保留\t制表符\n"

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]

        mock_fitz_open.return_value = mock_doc

        result = extract_text_from_pdf("whitespace.pdf")

        assert "文本前有空格" in result
        assert "\n" in result
        assert "\t" in result

    @patch("app.core.parse_doc.fitz.open")
    def test_extract_text_with_special_characters(self, mock_fitz_open):
        """测试提取包含特殊字符的文本"""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "特殊字符: @#$%^&*()[]{}|\\<>?/~`"

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]

        mock_fitz_open.return_value = mock_doc

        result = extract_text_from_pdf("special.pdf")

        assert result == "特殊字符: @#$%^&*()[]{}|\\<>?/~`"

    @patch("app.core.parse_doc.fitz.open")
    def test_extract_text_with_chinese_characters(self, mock_fitz_open):
        """测试提取中文文本"""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "这是一段中文文本,包含标点符号。还有更多内容!"

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]

        mock_fitz_open.return_value = mock_doc

        result = extract_text_from_pdf("chinese.pdf")

        assert result == "这是一段中文文本,包含标点符号。还有更多内容!"

    @patch("app.core.parse_doc.fitz.open")
    def test_fitz_open_exception(self, mock_fitz_open):
        """测试fitz.open抛出异常"""
        mock_fitz_open.side_effect = Exception("无法打开PDF文件")

        with pytest.raises(Exception, match="无法打开PDF文件"):
            extract_text_from_pdf("error.pdf")

    @patch("app.core.parse_doc.fitz.open")
    def test_get_text_exception(self, mock_fitz_open):
        """测试get_text方法抛出异常"""
        mock_page = MagicMock()
        mock_page.get_text.side_effect = Exception("无法提取文本")

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = [mock_page]

        mock_fitz_open.return_value = mock_doc

        with pytest.raises(Exception, match="无法提取文本"):
            extract_text_from_pdf("error.pdf")

    def test_pdf_file_with_path(self):
        """测试带路径的PDF文件"""
        with patch("app.core.parse_doc.fitz.open") as mock_fitz_open:
            mock_page = MagicMock()
            mock_page.get_text.return_value = "路径测试"

            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = [mock_page]

            mock_fitz_open.return_value = mock_doc

            result = extract_text_from_pdf("/path/to/file.pdf")

            assert result == "路径测试"
            mock_fitz_open.assert_called_once_with("/path/to/file.pdf")

    def test_case_sensitive_extension(self):
        """测试文件扩展名大小写"""
        # .PDF 大写扩展名应该被拒绝（当前实现）
        with pytest.raises(ValueError, match="非 PDF 文件"):
            extract_text_from_pdf("document.PDF")

        # 如果需要支持大小写不敏感，需要修改源代码


# ==================== 集成测试 ====================
# 这些测试使用真实的PDF文件,需要实际的文件系统访问

@pytest.mark.integration
class TestExtractTextFromPDFIntegration:
    """集成测试：使用真实PDF文件测试文档解析"""

    def test_extract_from_real_single_page_pdf(self):
        """测试从真实的单页PDF提取文本"""
        pdf_path = "tests/fixtures/test_sample.pdf"

        result = extract_text_from_pdf(pdf_path)

        assert result is not None
        assert len(result) > 0
        assert "test PDF file" in result
        assert "simple text for testing" in result

    def test_extract_from_real_multipage_pdf(self):
        """测试从真实的多页PDF提取文本"""
        pdf_path = "tests/fixtures/test_multipage.pdf"

        result = extract_text_from_pdf(pdf_path)

        assert result is not None
        assert len(result) > 0
        # 验证包含多页内容
        assert "page 1" in result or "This is page 1" in result
        assert "page 2" in result or "This is page 2" in result
        assert "page 3" in result or "This is page 3" in result

    def test_extract_from_real_chinese_pdf(self):
        """测试从真实的中文PDF提取文本"""
        pdf_path = "tests/fixtures/test_chinese.pdf"

        result = extract_text_from_pdf(pdf_path)

        assert result is not None
        assert len(result) > 0
        # 验证中文内容
        assert "中文" in result or "测试" in result

    def test_extract_from_project_pdf(self):
        """测试从项目中现有的PDF文件提取文本"""
        # 使用项目中实际存在的PDF文件
        pdf_path = "temp_files/联邦劳动法.pdf"

        try:
            result = extract_text_from_pdf(pdf_path)

            assert result is not None
            assert len(result) > 0
            print(f"成功提取了 {len(result)} 个字符")
            # 由于是法律文档，应该包含相关内容
            assert len(result) > 100  # 至少应该有一定长度的内容
        except FileNotFoundError:
            pytest.skip(f"PDF文件不存在: {pdf_path}")

    def test_extract_from_custom_path(self):
        """测试从自定义路径提取PDF - 演示如何指定路径"""
        # 这个测试展示如何使用自定义路径
        # 你可以修改下面的路径为你想测试的PDF文件路径

        custom_pdf_path = "upload_files/联邦劳动法_a4be5937-a659-48ca-9ecf-3130ded1f26c.pdf"

        try:
            result = extract_text_from_pdf(custom_pdf_path)

            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 0

            print(f"\n===== PDF解析结果 =====")
            print(f"文件路径: {custom_pdf_path}")
            print(f"提取字符数: {len(result)}")
            print(f"前200个字符: {result[:200]}")
            print("=" * 50)

        except FileNotFoundError:
            pytest.skip(f"PDF文件不存在: {custom_pdf_path}")
        except Exception as e:
            pytest.fail(f"解析PDF时出错: {str(e)}")

    def test_extract_with_absolute_path(self):
        """测试使用绝对路径"""
        import os

        # 获取当前工作目录
        base_dir = os.getcwd()
        pdf_path = os.path.join(base_dir, "tests/fixtures/test_sample.pdf")

        if os.path.exists(pdf_path):
            result = extract_text_from_pdf(pdf_path)
            assert result is not None
            assert len(result) > 0
        else:
            pytest.skip(f"PDF文件不存在: {pdf_path}")

    def test_nonexistent_pdf_file(self):
        """测试不存在的PDF文件"""
        with pytest.raises(Exception):  # fitz会抛出异常
            extract_text_from_pdf("nonexistent_file.pdf")
