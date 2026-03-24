"""
知识专家Agent

查询ChromaDB向量数据库，进行语义检索。
"""

from typing import Any, List, Dict, Optional

from .base_agent import BaseAgent


class KnowledgeExpertAgent(BaseAgent):
    """知识专家Agent - 查询向量知识库"""

    def __init__(self, llm_client=None, db_manager=None):
        super().__init__("knowledge_expert", llm_client)
        self._db_manager = db_manager

    @property
    def db_manager(self):
        if self._db_manager is None:
            from core.vector_store import db_manager
            self._db_manager = db_manager
        return self._db_manager

    async def execute(self, input_data: dict) -> Any:
        queries = input_data.get("queries", [])
        top_k = input_data.get("top_k", 3)
        filter_meta = input_data.get("filter_meta", None)

        all_results = []
        for query in queries:
            results = self.search(query, top_k, filter_meta)
            all_results.append({
                "query": query,
                "results": results,
                "count": len(results),
            })
        return {"source": "knowledge_base", "searches": all_results}

    def search(
        self,
        query: str,
        top_k: int = 3,
        filter_meta: Optional[Dict] = None,
    ) -> List[Dict]:
        """语义检索"""
        try:
            results = self.db_manager.search(
                query=query,
                top_k=top_k,
                filter_meta=filter_meta,
            )
            return results
        except Exception as e:
            self.logger.error(f"知识库检索失败: {e}")
            return []

    def format_context(self, results: List[Dict]) -> str:
        """将检索结果格式化为上下文文本"""
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            content = r.get("content", "")
            source = r.get("metadata", {}).get("source", "未知来源")
            parts.append(f"[来源{i}: {source}]\n{content}")
        return "\n\n".join(parts)
