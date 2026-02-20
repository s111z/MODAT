"""
文档切分模块

提供多种文档切分策略，用于将大文档切分成适合向量检索的小块。
支持按字符数、按段落、按句子等多种切分方式。
"""

from typing import List, Dict, Optional, Any
import re


class TextSplitter:
    """文本切分器基类"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n"
    ):
        """
        初始化文本切分器

        Args:
            chunk_size: 每个chunk的最大字符数
            chunk_overlap: chunk之间的重叠字符数
            separator: 分隔符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap必须小于chunk_size")

    def split_text(self, text: str) -> List[str]:
        """
        切分文本

        Args:
            text: 要切分的文本

        Returns:
            切分后的文本块列表
        """
        raise NotImplementedError("子类必须实现split_text方法")

    def create_chunks_with_metadata(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        切分文本并添加元数据

        Args:
            text: 要切分的文本
            metadata: 基础元数据

        Returns:
            包含文本和元数据的chunk列表
        """
        chunks = self.split_text(text)
        metadata = metadata or {}

        result = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk)
            }
            result.append({
                "text": chunk,
                "metadata": chunk_metadata
            })

        return result


class CharacterTextSplitter(TextSplitter):
    """按字符数切分文本"""

    def split_text(self, text: str) -> List[str]:
        """
        按字符数切分文本，保持重叠

        Args:
            text: 要切分的文本

        Returns:
            切分后的文本块列表
        """
        if not text:
            return []

        # 先按分隔符切分
        if self.separator:
            splits = text.split(self.separator)
        else:
            splits = [text]

        # 合并成适当大小的chunks
        chunks = []
        current_chunk = []
        current_size = 0

        for split in splits:
            split_size = len(split)

            # 如果单个split就超过chunk_size，需要强制切分
            if split_size > self.chunk_size:
                # 先保存当前chunk
                if current_chunk:
                    chunks.append(self.separator.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 强制切分大块
                for i in range(0, split_size, self.chunk_size - self.chunk_overlap):
                    chunks.append(split[i:i + self.chunk_size])
                continue

            # 检查是否需要开始新chunk
            if current_size + split_size + len(self.separator) > self.chunk_size:
                if current_chunk:
                    chunks.append(self.separator.join(current_chunk))

                # 保留重叠部分
                overlap_text = self.separator.join(current_chunk)
                if len(overlap_text) > self.chunk_overlap:
                    overlap_text = overlap_text[-self.chunk_overlap:]
                    current_chunk = [overlap_text]
                    current_size = len(overlap_text)
                else:
                    current_chunk = []
                    current_size = 0

            current_chunk.append(split)
            current_size += split_size + len(self.separator)

        # 添加最后一个chunk
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return [chunk.strip() for chunk in chunks if chunk.strip()]


class ParagraphTextSplitter(TextSplitter):
    """按段落切分文本"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        paragraph_separator: str = "\n\n"
    ):
        """
        初始化段落切分器

        Args:
            chunk_size: 每个chunk的最大字符数
            chunk_overlap: chunk之间的重叠字符数
            paragraph_separator: 段落分隔符
        """
        super().__init__(chunk_size, chunk_overlap, paragraph_separator)
        self.paragraph_separator = paragraph_separator

    def split_text(self, text: str) -> List[str]:
        """
        按段落切分文本

        Args:
            text: 要切分的文本

        Returns:
            切分后的文本块列表
        """
        if not text:
            return []

        # 按段落分隔符切分
        paragraphs = text.split(self.paragraph_separator)

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_size = len(paragraph)

            # 如果单个段落超过chunk_size，使用字符切分器
            if paragraph_size > self.chunk_size:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(self.paragraph_separator.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 使用字符切分器处理大段落
                char_splitter = CharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separator="\n"
                )
                paragraph_chunks = char_splitter.split_text(paragraph)
                chunks.extend(paragraph_chunks)
                continue

            # 检查是否需要开始新chunk
            if current_size + paragraph_size > self.chunk_size:
                if current_chunk:
                    chunks.append(self.paragraph_separator.join(current_chunk))
                    current_chunk = [paragraph]
                    current_size = paragraph_size
                else:
                    current_chunk = [paragraph]
                    current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size + len(self.paragraph_separator)

        # 添加最后一个chunk
        if current_chunk:
            chunks.append(self.paragraph_separator.join(current_chunk))

        return [chunk.strip() for chunk in chunks if chunk.strip()]


class SentenceTextSplitter(TextSplitter):
    """按句子切分文本"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        language: str = "zh"
    ):
        """
        初始化句子切分器

        Args:
            chunk_size: 每个chunk的最大字符数
            chunk_overlap: chunk之间的重叠字符数
            language: 语言，zh(中文)或en(英文)
        """
        super().__init__(chunk_size, chunk_overlap, "")
        self.language = language

        # 根据语言选择句子分隔符
        if language == "zh":
            self.sentence_endings = r'[。！？；]'
        else:
            self.sentence_endings = r'[.!?;]'

    def split_text(self, text: str) -> List[str]:
        """
        按句子切分文本

        Args:
            text: 要切分的文本

        Returns:
            切分后的文本块列表
        """
        if not text:
            return []

        # 按句子分隔符切分
        sentences = re.split(f'({self.sentence_endings})', text)

        # 重新组合句子（保留标点）
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])

        # 如果有剩余部分
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            combined_sentences.append(sentences[-1])

        # 合并成适当大小的chunks
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_size = len(sentence)

            # 如果单个句子超过chunk_size，使用字符切分
            if sentence_size > self.chunk_size:
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 对长句子进行字符切分
                for i in range(0, sentence_size, self.chunk_size - self.chunk_overlap):
                    chunks.append(sentence[i:i + self.chunk_size])
                continue

            # 检查是否需要开始新chunk
            if current_size + sentence_size > self.chunk_size:
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = [sentence]
                    current_size = sentence_size
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # 添加最后一个chunk
        if current_chunk:
            chunks.append("".join(current_chunk))

        return [chunk.strip() for chunk in chunks if chunk.strip()]


class RecursiveCharacterTextSplitter(TextSplitter):
    """递归字符文本切分器

    尝试按不同层级的分隔符递归切分，从大到小：段落 -> 句子 -> 单词 -> 字符
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        初始化递归切分器

        Args:
            chunk_size: 每个chunk的最大字符数
            chunk_overlap: chunk之间的重叠字符数
            separators: 分隔符列表，按优先级排序
        """
        super().__init__(chunk_size, chunk_overlap, "")

        if separators is None:
            # 默认分隔符：段落 -> 换行 -> 空格 -> 字符
            self.separators = ["\n\n", "\n", " ", ""]
        else:
            self.separators = separators

    def split_text(self, text: str) -> List[str]:
        """
        递归切分文本

        Args:
            text: 要切分的文本

        Returns:
            切分后的文本块列表
        """
        if not text:
            return []

        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """
        递归切分文本的内部方法

        Args:
            text: 要切分的文本
            separators: 当前可用的分隔符列表

        Returns:
            切分后的文本块列表
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        # 尝试使用当前分隔符
        separator = separators[0] if separators else ""

        if separator == "":
            # 最后一级：强制按字符切分
            chunks = []
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunks.append(text[i:i + self.chunk_size])
            return chunks

        # 使用当前分隔符切分
        splits = text.split(separator)

        chunks = []
        current_chunk = []
        current_size = 0

        for split in splits:
            split_size = len(split)

            # 如果split太大，使用下一级分隔符
            if split_size > self.chunk_size:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # 递归使用下一级分隔符
                sub_chunks = self._split_text_recursive(split, separators[1:])
                chunks.extend(sub_chunks)
                continue

            # 检查是否需要开始新chunk
            if current_size + split_size + len(separator) > self.chunk_size:
                if current_chunk:
                    chunks.append(separator.join(current_chunk))
                    current_chunk = [split]
                    current_size = split_size
                else:
                    current_chunk = [split]
                    current_size = split_size
            else:
                current_chunk.append(split)
                current_size += split_size + len(separator)

        # 添加最后一个chunk
        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return [chunk.strip() for chunk in chunks if chunk.strip()]


# 便捷函数
def split_text_by_characters(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separator: str = "\n"
) -> List[str]:
    """
    按字符数切分文本的便捷函数

    Args:
        text: 要切分的文本
        chunk_size: 每个chunk的最大字符数
        chunk_overlap: chunk之间的重叠字符数
        separator: 分隔符

    Returns:
        切分后的文本块列表
    """
    splitter = CharacterTextSplitter(chunk_size, chunk_overlap, separator)
    return splitter.split_text(text)


def split_text_by_paragraphs(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[str]:
    """
    按段落切分文本的便捷函数

    Args:
        text: 要切分的文本
        chunk_size: 每个chunk的最大字符数
        chunk_overlap: chunk之间的重叠字符数

    Returns:
        切分后的文本块列表
    """
    splitter = ParagraphTextSplitter(chunk_size, chunk_overlap)
    return splitter.split_text(text)


def split_text_by_sentences(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    language: str = "zh"
) -> List[str]:
    """
    按句子切分文本的便捷函数

    Args:
        text: 要切分的文本
        chunk_size: 每个chunk的最大字符数
        chunk_overlap: chunk之间的重叠字符数
        language: 语言，zh(中文)或en(英文)

    Returns:
        切分后的文本块列表
    """
    splitter = SentenceTextSplitter(chunk_size, chunk_overlap, language)
    return splitter.split_text(text)


def split_text_recursive(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    separators: Optional[List[str]] = None
) -> List[str]:
    """
    递归切分文本的便捷函数

    Args:
        text: 要切分的文本
        chunk_size: 每个chunk的最大字符数
        chunk_overlap: chunk之间的重叠字符数
        separators: 分隔符列表，按优先级排序

    Returns:
        切分后的文本块列表
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size, chunk_overlap, separators)
    return splitter.split_text(text)
