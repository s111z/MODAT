"""
信息脱敏Agent

对用户输入进行PII检测与脱敏处理，响应阶段还原。
"""

import re
from typing import Any

from .base_agent import BaseAgent


class DesensitizeAgent(BaseAgent):
    """信息脱敏Agent"""

    PII_PATTERNS = {
        "PHONE": r"1[3-9]\d{9}",
        "ID_CARD": r"\d{17}[\dXx]",
        "EMAIL": r"[\w.-]+@[\w.-]+\.\w+",
        "BANK_CARD": r"\d{16,19}",
    }

    def __init__(self, llm_client=None):
        super().__init__("desensitize", llm_client)

    async def execute(self, input_data: dict) -> Any:
        text = input_data.get("text", "")
        desensitized_text, mapping = self.desensitize(text)
        return {
            "text": desensitized_text,
            "mapping": mapping,
            "has_pii": len(mapping) > 0,
        }

    def desensitize(self, text: str) -> tuple[str, dict]:
        """对文本进行脱敏，返回(脱敏文本, 映射表)"""
        mapping = {}
        counter = 0
        for pii_type, pattern in self.PII_PATTERNS.items():
            for match in re.finditer(pattern, text):
                original = match.group()
                if original in [v for v in mapping.values()]:
                    continue
                placeholder = f"[{pii_type}_{counter}]"
                mapping[placeholder] = original
                text = text.replace(original, placeholder)
                counter += 1
        return text, mapping

    @staticmethod
    def restore(text: str, mapping: dict) -> str:
        """根据映射表还原脱敏文本"""
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text
