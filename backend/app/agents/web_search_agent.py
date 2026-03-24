"""
Web搜索Agent

使用DuckDuckGo进行网络搜索，格式化结果。
"""

from typing import Any, List, Dict

from .base_agent import BaseAgent


class WebSearchAgent(BaseAgent):
    """Web搜索Agent"""

    def __init__(self, llm_client=None, search_client=None):
        super().__init__("web_search", llm_client)
        self._search_client = search_client

    @property
    def search_client(self):
        if self._search_client is None:
            from core.search import search_client
            self._search_client = search_client
        return self._search_client

    async def execute(self, input_data: dict) -> Any:
        queries = input_data.get("queries", [])
        max_results = input_data.get("max_results", 5)

        all_results = []
        for query in queries:
            results = self.search(query, max_results)
            all_results.append({
                "query": query,
                "results": results,
                "count": len(results),
            })
        return {"source": "web_search", "searches": all_results}

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """执行网络搜索"""
        try:
            results = self.search_client.search(query, max_results=max_results)
            return results
        except Exception as e:
            self.logger.error(f"网络搜索失败: {e}")
            return []

    def format_context(self, results: List[Dict]) -> str:
        """将搜索结果格式化为上下文文本"""
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")
            parts.append(f"[网络来源{i}: {title}]({url})\n{content}")
        return "\n\n".join(parts)
