"""
文档解析Agent

支持多格式文档解析：PDF, DOCX, DOC, TXT
"""

import os
from typing import Any

from .base_agent import BaseAgent


class DocParserAgent(BaseAgent):
    """文档解析Agent"""

    def __init__(self, llm_client=None):
        super().__init__("doc_parser", llm_client)

    async def execute(self, input_data: dict) -> Any:
        filepath = input_data.get("filepath", "")
        return self.parse(filepath)

    def parse(self, filepath: str) -> dict:
        """解析文档，返回文本内容"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        parsers = {
            ".pdf": self._parse_pdf,
            ".docx": self._parse_docx,
            ".txt": self._parse_txt,
        }

        parser = parsers.get(ext)
        if not parser:
            raise ValueError(f"不支持的文件类型: {ext}")

        text = parser(filepath)
        return {
            "text": text,
            "file_type": ext,
            "char_count": len(text),
            "filename": os.path.basename(filepath),
        }

    def _parse_pdf(self, filepath: str) -> str:
        """解析PDF文件"""
        import fitz
        doc = fitz.open(filepath)
        text = "".join([page.get_text() for page in doc])
        doc.close()
        return text

    def _parse_docx(self, filepath: str) -> str:
        """解析DOCX文件"""
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # 也提取表格内容
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        return "\n\n".join(paragraphs)

    def _parse_txt(self, filepath: str) -> str:
        """解析纯文本文件"""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
