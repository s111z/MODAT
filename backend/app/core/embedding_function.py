"""
ChromaDB 自定义 Embedding Function

将本地 vllm Embedding 模型集成到 ChromaDB
"""

from typing import List, cast
from chromadb import Documents, EmbeddingFunction, Embeddings
from .embedding import get_embedding_model, EmbeddingModel
import os

class VLLMEmbeddingFunction(EmbeddingFunction[Documents]):
    """ChromaDB 自定义 Embedding Function

    使用本地 vllm 模型为 ChromaDB 提供 embeddings
    """

    def __init__(
        self,
        model_name_or_path: str = "Qwen3-Embedding-0.6B",
        device: str = "cuda",
        task_description: str = 'Given a web search query, retrieve relevant passages that answer the query',
        **kwargs
    ):
        """
        初始化

        Args:
            model_name_or_path: 模型名称（HuggingFace）或本地路径
                - HuggingFace: "Qwen/Qwen3-Embedding-0.6B"
                - 本地路径: "/path/to/local/model"
            device: 设备类型
            task_description: 默认任务描述
            **kwargs: 传递给模型的其他参数
        """
        base_dir = os.getenv("MODEL_BASE_DIR", "/root/modelparams")
        self.model_name = os.path.join(base_dir, model_name)
        self.device = device
        self.task_description = task_description
        self.kwargs = kwargs

        # 延迟加载模型（避免初始化时的开销）
        self._model: EmbeddingModel = None

    @property
    def model(self) -> EmbeddingModel:
        """延迟加载模型"""
        if self._model is None:
            self._model = get_embedding_model(
                model_name=self.model_name,
                device=self.device,
                **self.kwargs
            )
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        """
        ChromaDB 调用接口

        Args:
            input: 文档列表

        Returns:
            embeddings 列表
        """
        # ChromaDB 传入的是文档，不添加指令
        embeddings = self.model.encode_documents(
            input,
            return_tensors="np"
        )

        # 转换为 ChromaDB 需要的格式
        return cast(Embeddings, embeddings.tolist())


class VLLMQueryEmbeddingFunction:
    """用于查询的 Embedding Function（添加指令）

    注意：这个类不是 ChromaDB 的 EmbeddingFunction，
    而是用于在查询时手动生成带指令的 embeddings
    """

    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen3-Embedding-0.6B",
        device: str = "cuda",
        task_description: str = 'Given a web search query, retrieve relevant passages that answer the query',
        **kwargs
    ):
        """
        初始化

        Args:
            model_name_or_path: 模型名称（HuggingFace）或本地路径
                - HuggingFace: "Qwen/Qwen3-Embedding-0.6B"
                - 本地路径: "/path/to/local/model"
            device: 设备类型
            task_description: 任务描述
            **kwargs: 传递给模型的其他参数
        """
        self.model_name = model_name_or_path
        self.device = device
        self.task_description = task_description
        self.kwargs = kwargs

        self._model: EmbeddingModel = None

    @property
    def model(self) -> EmbeddingModel:
        """延迟加载模型"""
        if self._model is None:
            self._model = get_embedding_model(
                model_name=self.model_name,
                device=self.device,
                **self.kwargs
            )
        return self._model

    def embed_query(self, query: str) -> List[float]:
        """
        编码查询（带指令）

        Args:
            query: 查询文本

        Returns:
            embedding 向量
        """
        embeddings = self.model.encode_queries(
            query,
            task_description=self.task_description,
            return_tensors="np"
        )

        # 返回第一个查询的 embedding
        return embeddings[0].tolist()

    def embed_queries(self, queries: List[str]) -> List[List[float]]:
        """
        批量编码查询（带指令）

        Args:
            queries: 查询列表

        Returns:
            embeddings 列表
        """
        embeddings = self.model.encode_queries(
            queries,
            task_description=self.task_description,
            return_tensors="np"
        )

        return embeddings.tolist()
