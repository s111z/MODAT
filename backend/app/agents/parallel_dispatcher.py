"""
并行分发组件

将查询并行分发到多个数据源（知识库、网络搜索），聚合结果。
"""

import asyncio
from typing import Any, List, Dict

from .base_agent import BaseAgent
from .knowledge_expert_agent import KnowledgeExpertAgent
from .web_search_agent import WebSearchAgent


class ParallelDispatcher(BaseAgent):
    """并行分发组件"""

    def __init__(self, llm_client=None):
        super().__init__("parallel_dispatcher", llm_client)
        self.knowledge_agent = KnowledgeExpertAgent(llm_client)
        self.web_search_agent = WebSearchAgent(llm_client)

    async def execute(self, input_data: dict) -> Any:
        queries = input_data.get("queries", [])
        sources = input_data.get("sources", ["knowledge", "web"])
        top_k = input_data.get("top_k", 3)

        return await self.dispatch(queries, sources, top_k)

    async def dispatch(
        self,
        queries: List[str],
        sources: List[str],
        top_k: int = 3,
    ) -> dict:
        """并行分发查询到多个数据源"""
        tasks = {}

        if "knowledge" in sources:
            tasks["knowledge"] = self.knowledge_agent.execute({
                "queries": queries,
                "top_k": top_k,
            })

        if "web" in sources:
            tasks["web"] = self.web_search_agent.execute({
                "queries": queries,
                "max_results": top_k,
            })

        # 并行执行
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )

        output = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                self.logger.error(f"{key} 查询失败: {result}")
                output[key] = {"source": key, "searches": [], "error": str(result)}
            else:
                output[key] = result

        return output

    def collect_all_results(self, dispatch_output: dict) -> tuple[list, list]:
        """从分发结果中收集所有检索结果，返回 (knowledge_results, web_results)"""
        knowledge_results = []
        web_results = []

        kb_data = dispatch_output.get("knowledge", {})
        for search in kb_data.get("searches", []):
            knowledge_results.extend(search.get("results", []))

        web_data = dispatch_output.get("web", {})
        for search in web_data.get("searches", []):
            web_results.extend(search.get("results", []))

        return knowledge_results, web_results
