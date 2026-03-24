"""
Agent基类模块

所有Agent继承BaseAgent，统一提供：
- 异步/同步LLM调用
- 日志记录与执行耗时统计
- 异常捕获与优雅降级
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging
import time
import json


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str, llm_client=None):
        self.name = name
        self.llm = llm_client
        self.logger = logging.getLogger(f"agent.{name}")

    def _get_llm(self):
        """延迟获取LLM客户端"""
        if self.llm is None:
            from core.llm import deepseek_client
            self.llm = deepseek_client
        return self.llm

    async def run(self, input_data: dict) -> dict:
        """统一执行入口"""
        start = time.time()
        self.logger.info(f"[{self.name}] 开始执行")
        try:
            result = await self.execute(input_data)
            elapsed = time.time() - start
            self.logger.info(f"[{self.name}] 执行完成, 耗时: {elapsed:.2f}s")
            return {
                "status": "success",
                "agent": self.name,
                "data": result,
                "elapsed": elapsed,
            }
        except Exception as e:
            elapsed = time.time() - start
            self.logger.error(f"[{self.name}] 执行失败: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "elapsed": elapsed,
            }

    @abstractmethod
    async def execute(self, input_data: dict) -> Any:
        """子类实现具体逻辑"""
        pass

    def llm_generate(self, prompt: str, context: str = None, system_message: str = None) -> str:
        """同步调用LLM生成回复"""
        llm = self._get_llm()
        return llm.generate_response(
            prompt=prompt,
            context=context,
            system_message=system_message,
        )

    def llm_generate_json(self, prompt: str, context: str = None, system_message: str = None) -> dict:
        """调用LLM并解析JSON结果"""
        raw = self.llm_generate(prompt, context, system_message)
        # 尝试从回复中提取JSON
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        return json.loads(raw.strip())
