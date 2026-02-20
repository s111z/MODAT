"""
向量数据库配置

提供不同 embedding 模型的配置选项
"""

import os
from typing import Literal

# Embedding 模型配置
EMBEDDING_MODEL_TYPE = os.getenv("EMBEDDING_MODEL_TYPE", "vllm")  # vllm, default, openai
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "Qwen/Qwen3-Embedding-0.6B")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")  # cuda, cpu

# 任务描述（用于查询）
DEFAULT_TASK_DESCRIPTION = os.getenv(
    "EMBEDDING_TASK_DESCRIPTION",
    'Given a web search query, retrieve relevant passages that answer the query'
)

# ChromaDB 配置
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "mota_knowledge")


def get_embedding_function():
    """
    根据配置获取 embedding function

    Returns:
        ChromaDB compatible embedding function
    """
    if EMBEDDING_MODEL_TYPE == "vllm":
        # 使用本地 vllm 模型
        from .embedding_function import VLLMEmbeddingFunction

        return VLLMEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME,
            device=EMBEDDING_DEVICE,
            task_description=DEFAULT_TASK_DESCRIPTION
        )

    elif EMBEDDING_MODEL_TYPE == "openai":
        # 使用 OpenAI embedding
        from chromadb.utils import embedding_functions

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("使用 OpenAI embedding 需要设置 OPENAI_API_KEY 环境变量")

        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )

    else:
        # 使用默认的 all-MiniLM-L6-v2
        from chromadb.utils import embedding_functions

        print("⚠️  [警告] 使用默认 embedding 模型（all-MiniLM-L6-v2），对中文支持一般")
        return embedding_functions.DefaultEmbeddingFunction()


def get_query_embedding_function():
    """
    获取查询专用的 embedding function（带指令）

    Returns:
        Query embedding function
    """
    if EMBEDDING_MODEL_TYPE == "vllm":
        from .embedding_function import VLLMQueryEmbeddingFunction

        return VLLMQueryEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME,
            device=EMBEDDING_DEVICE,
            task_description=DEFAULT_TASK_DESCRIPTION
        )

    else:
        # 其他类型不需要特殊处理
        return None
