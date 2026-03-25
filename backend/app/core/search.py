from typing import List, Dict, Any
from duckduckgo_search import DDGS
from core.config import settings

class SearchClient:
    """搜索客户端，使用DuckDuckGo"""
    
    def __init__(self, max_results: int = None):
        self.max_results = max_results or settings.search_max_results
    
    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        使用DuckDuckGo搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        try:
            max_results = max_results or self.max_results
            
            # 使用DuckDuckGo搜索
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    max_results=max_results
                ))
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "content": result.get("body", ""),
                    "source": "duckduckgo"
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []
    
    def search_news(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        搜索新闻
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            新闻结果列表
        """
        try:
            max_results = max_results or self.max_results
            
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    query,
                    max_results=max_results
                ))
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("body", ""),
                    "date": result.get("date", ""),
                    "source": "duckduckgo_news"
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"新闻搜索失败: {str(e)}")
            return []

# 全局搜索客户端实例
search_client = SearchClient()

if __name__ == "__main__":
    results = search_client.search("人工智能的未来")
    for it in results:
        print(it)