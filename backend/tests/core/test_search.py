import pytest
from unittest.mock import MagicMock, patch
from app.core.search import SearchClient


class TestSearchClient:
    """测试SearchClient类"""

    @patch("app.core.search.settings")
    def test_init_default(self, mock_settings):
        """测试默认初始化"""
        mock_settings.search_max_results = 5

        client = SearchClient()

        assert client.max_results == 5

    @patch("app.core.search.settings")
    def test_init_with_custom_max_results(self, mock_settings):
        """测试自定义最大结果数初始化"""
        mock_settings.search_max_results = 5

        client = SearchClient(max_results=10)

        assert client.max_results == 10

    @patch("app.core.search.DDGS")
    def test_search_success(self, mock_ddgs_class):
        """测试成功搜索"""
        # 模拟搜索结果
        mock_results = [
            {
                "title": "结果1",
                "href": "https://example.com/1",
                "body": "这是第一个结果的内容"
            },
            {
                "title": "结果2",
                "href": "https://example.com/2",
                "body": "这是第二个结果的内容"
            }
        ]

        # 模拟DDGS实例
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = iter(mock_results)
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient(max_results=5)
        results = client.search("测试查询")

        assert len(results) == 2
        assert results[0]["title"] == "结果1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["content"] == "这是第一个结果的内容"
        assert results[0]["source"] == "duckduckgo"

        assert results[1]["title"] == "结果2"
        assert results[1]["url"] == "https://example.com/2"

        mock_ddgs_instance.text.assert_called_once_with("测试查询", max_results=5)

    @patch("app.core.search.DDGS")
    def test_search_with_custom_max_results(self, mock_ddgs_class):
        """测试使用自定义最大结果数搜索"""
        mock_results = [{"title": "结果", "href": "url", "body": "内容"}]

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = iter(mock_results)
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient(max_results=5)
        results = client.search("查询", max_results=3)

        mock_ddgs_instance.text.assert_called_once_with("查询", max_results=3)

    @patch("app.core.search.DDGS")
    def test_search_empty_results(self, mock_ddgs_class):
        """测试搜索无结果"""
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = iter([])
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient()
        results = client.search("无结果查询")

        assert results == []

    @patch("app.core.search.DDGS")
    @patch("builtins.print")
    def test_search_exception(self, mock_print, mock_ddgs_class):
        """测试搜索异常处理"""
        mock_ddgs_class.return_value.__enter__.side_effect = Exception("网络错误")

        client = SearchClient()
        results = client.search("错误查询")

        assert results == []
        mock_print.assert_called_once()
        assert "搜索失败" in str(mock_print.call_args)

    @patch("app.core.search.DDGS")
    def test_search_missing_fields(self, mock_ddgs_class):
        """测试处理缺少字段的搜索结果"""
        mock_results = [
            {
                "title": "有标题",
                # 缺少href
                "body": "有内容"
            },
            {
                # 缺少title
                "href": "https://example.com",
                # 缺少body
            }
        ]

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = iter(mock_results)
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient()
        results = client.search("查询")

        assert len(results) == 2
        assert results[0]["title"] == "有标题"
        assert results[0]["url"] == ""
        assert results[0]["content"] == "有内容"

        assert results[1]["title"] == ""
        assert results[1]["url"] == "https://example.com"
        assert results[1]["content"] == ""

    @patch("app.core.search.DDGS")
    def test_search_news_success(self, mock_ddgs_class):
        """测试成功搜索新闻"""
        mock_results = [
            {
                "title": "新闻1",
                "url": "https://news.com/1",
                "body": "新闻内容1",
                "date": "2024-01-01"
            },
            {
                "title": "新闻2",
                "url": "https://news.com/2",
                "body": "新闻内容2",
                "date": "2024-01-02"
            }
        ]

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.news.return_value = iter(mock_results)
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient(max_results=5)
        results = client.search_news("新闻查询")

        assert len(results) == 2
        assert results[0]["title"] == "新闻1"
        assert results[0]["url"] == "https://news.com/1"
        assert results[0]["content"] == "新闻内容1"
        assert results[0]["date"] == "2024-01-01"
        assert results[0]["source"] == "duckduckgo_news"

        mock_ddgs_instance.news.assert_called_once_with("新闻查询", max_results=5)

    @patch("app.core.search.DDGS")
    def test_search_news_with_custom_max_results(self, mock_ddgs_class):
        """测试使用自定义最大结果数搜索新闻"""
        mock_results = [{"title": "新闻", "url": "url", "body": "内容", "date": "2024-01-01"}]

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.news.return_value = iter(mock_results)
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient(max_results=5)
        results = client.search_news("查询", max_results=8)

        mock_ddgs_instance.news.assert_called_once_with("查询", max_results=8)

    @patch("app.core.search.DDGS")
    def test_search_news_empty_results(self, mock_ddgs_class):
        """测试搜索新闻无结果"""
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.news.return_value = iter([])
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient()
        results = client.search_news("无结果查询")

        assert results == []

    @patch("app.core.search.DDGS")
    @patch("builtins.print")
    def test_search_news_exception(self, mock_print, mock_ddgs_class):
        """测试搜索新闻异常处理"""
        mock_ddgs_class.return_value.__enter__.side_effect = Exception("API错误")

        client = SearchClient()
        results = client.search_news("错误查询")

        assert results == []
        mock_print.assert_called_once()
        assert "新闻搜索失败" in str(mock_print.call_args)

    @patch("app.core.search.DDGS")
    def test_search_news_missing_fields(self, mock_ddgs_class):
        """测试处理缺少字段的新闻结果"""
        mock_results = [
            {
                "title": "新闻",
                # 缺少其他字段
            }
        ]

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.news.return_value = iter(mock_results)
        mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs_instance

        client = SearchClient()
        results = client.search_news("查询")

        assert len(results) == 1
        assert results[0]["title"] == "新闻"
        assert results[0]["url"] == ""
        assert results[0]["content"] == ""
        assert results[0]["date"] == ""
        assert results[0]["source"] == "duckduckgo_news"

    @patch("app.core.search.settings")
    @patch("app.core.search.SearchClient")
    def test_global_search_client(self, mock_client_class, mock_settings):
        """测试全局search_client实例"""
        from app.core.search import search_client
        assert search_client is not None
