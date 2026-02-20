"""
本地 Embedding 模型管理模块

使用 vllm 加载和管理本地 embedding 模型（如 Qwen3-Embedding-0.6B）
支持查询编码、文档编码和相似度计算
"""

import torch
from typing import List, Optional, Union, Tuple
from vllm import LLM
import numpy as np


class EmbeddingModel:
    """本地 Embedding 模型封装类

    使用 vllm 加载本地 embedding 模型，提供文本编码和相似度计算功能。
    支持为查询添加任务指令，优化检索效果。
    """

    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen3-Embedding-0.6B",
        device: str = "cuda",
        trust_remote_code: bool = True,
        **kwargs
    ):
        """
        初始化 Embedding 模型

        Args:
            model_name_or_path: 模型名称（HuggingFace）或本地路径
                - HuggingFace: "Qwen/Qwen3-Embedding-0.6B"
                - 本地路径: "/path/to/local/model"
            device: 设备类型 (cuda/cpu)
            trust_remote_code: 是否信任远程代码
            **kwargs: 传递给 vllm.LLM 的其他参数
        """
        self.model_name = model_name_or_path
        self.device = device

        # 检查是否为本地路径
        import os
        if os.path.exists(model_name_or_path):
            print(f"🔄 正在从本地路径加载模型: {model_name_or_path}")
        else:
            print(f"🔄 正在从 HuggingFace 加载模型: {model_name_or_path}")

        print(f"📍 设备: {device}")

        try:
            # 初始化 vllm LLM
            self.model = LLM(
                model=model_name_or_path,
                task="embed",
                trust_remote_code=trust_remote_code,
                **kwargs
            )
            print(f"✅ 模型加载成功!")

        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise

    def get_detailed_instruct(self, task_description: str, query: str) -> str:
        """
        为查询添加任务指令

        Args:
            task_description: 任务描述
            query: 查询文本

        Returns:
            带指令的查询文本
        """
        return f'Instruct: {task_description}\nQuery: {query}'

    def encode_queries(
        self,
        queries: Union[str, List[str]],
        task_description: str = 'Given a web search query, retrieve relevant passages that answer the query',
        return_tensors: str = "pt"
    ) -> Union[torch.Tensor, np.ndarray]:
        """
        编码查询文本（带任务指令）

        Args:
            queries: 单个查询或查询列表
            task_description: 任务描述
            return_tensors: 返回格式 ("pt" for PyTorch, "np" for NumPy)

        Returns:
            查询的 embedding 向量
        """
        # 标准化输入
        if isinstance(queries, str):
            queries = [queries]

        # 为每个查询添加指令
        instruct_queries = [
            self.get_detailed_instruct(task_description, q)
            for q in queries
        ]

        # 编码
        embeddings = self._encode(instruct_queries)

        if return_tensors == "np":
            return embeddings.cpu().numpy()
        return embeddings

    def encode_documents(
        self,
        documents: Union[str, List[str]],
        return_tensors: str = "pt"
    ) -> Union[torch.Tensor, np.ndarray]:
        """
        编码文档文本（不添加指令）

        Args:
            documents: 单个文档或文档列表
            return_tensors: 返回格式 ("pt" for PyTorch, "np" for NumPy)

        Returns:
            文档的 embedding 向量
        """
        # 标准化输入
        if isinstance(documents, str):
            documents = [documents]

        # 编码（不添加指令）
        embeddings = self._encode(documents)

        if return_tensors == "np":
            return embeddings.cpu().numpy()
        return embeddings

    def encode(
        self,
        texts: Union[str, List[str]],
        add_instruction: bool = False,
        task_description: Optional[str] = None,
        return_tensors: str = "pt"
    ) -> Union[torch.Tensor, np.ndarray]:
        """
        通用编码方法

        Args:
            texts: 单个文本或文本列表
            add_instruction: 是否添加任务指令
            task_description: 任务描述（如果 add_instruction=True）
            return_tensors: 返回格式 ("pt" for PyTorch, "np" for NumPy)

        Returns:
            文本的 embedding 向量
        """
        if add_instruction:
            if task_description is None:
                task_description = 'Given a web search query, retrieve relevant passages that answer the query'
            return self.encode_queries(texts, task_description, return_tensors)
        else:
            return self.encode_documents(texts, return_tensors)

    def _encode(self, texts: List[str]) -> torch.Tensor:
        """
        内部编码方法

        Args:
            texts: 文本列表

        Returns:
            PyTorch tensor 格式的 embeddings
        """
        try:
            # 使用 vllm 编码
            outputs = self.model.embed(texts)

            # 提取 embeddings
            embeddings = torch.tensor([o.outputs.embedding for o in outputs])

            return embeddings

        except Exception as e:
            print(f"❌ 编码失败: {e}")
            raise

    def compute_similarity(
        self,
        query_embeddings: Union[torch.Tensor, np.ndarray],
        doc_embeddings: Union[torch.Tensor, np.ndarray],
        normalize: bool = True
    ) -> Union[torch.Tensor, np.ndarray]:
        """
        计算查询和文档之间的相似度

        Args:
            query_embeddings: 查询的 embeddings [num_queries, embedding_dim]
            doc_embeddings: 文档的 embeddings [num_docs, embedding_dim]
            normalize: 是否归一化（余弦相似度）

        Returns:
            相似度矩阵 [num_queries, num_docs]
        """
        # 转换为 PyTorch tensor
        if isinstance(query_embeddings, np.ndarray):
            query_embeddings = torch.from_numpy(query_embeddings)
        if isinstance(doc_embeddings, np.ndarray):
            doc_embeddings = torch.from_numpy(doc_embeddings)

        # 归一化（余弦相似度）
        if normalize:
            query_embeddings = torch.nn.functional.normalize(query_embeddings, p=2, dim=1)
            doc_embeddings = torch.nn.functional.normalize(doc_embeddings, p=2, dim=1)

        # 计算相似度（点积）
        scores = query_embeddings @ doc_embeddings.T

        return scores

    def search(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
        task_description: Optional[str] = None
    ) -> List[Tuple[int, float, str]]:
        """
        在文档集合中搜索最相关的文档

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回的文档数量
            task_description: 任务描述

        Returns:
            (索引, 相似度分数, 文档内容) 的列表
        """
        # 编码查询
        query_emb = self.encode_queries(
            query,
            task_description=task_description or 'Given a web search query, retrieve relevant passages that answer the query'
        )

        # 编码文档
        doc_embs = self.encode_documents(documents)

        # 计算相似度
        scores = self.compute_similarity(query_emb, doc_embs)

        # 获取分数（第一个查询的所有文档分数）
        scores = scores[0].tolist()

        # 排序并获取 top_k
        indexed_scores = [(i, score, documents[i]) for i, score in enumerate(scores)]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        return indexed_scores[:top_k]

    def batch_encode_queries(
        self,
        queries: List[str],
        task_description: str = 'Given a web search query, retrieve relevant passages that answer the query',
        batch_size: int = 32,
        return_tensors: str = "pt"
    ) -> Union[torch.Tensor, np.ndarray]:
        """
        批量编码查询（用于大规模查询）

        Args:
            queries: 查询列表
            task_description: 任务描述
            batch_size: 批次大小
            return_tensors: 返回格式

        Returns:
            所有查询的 embeddings
        """
        all_embeddings = []

        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            batch_embs = self.encode_queries(batch, task_description, return_tensors="pt")
            all_embeddings.append(batch_embs)

        # 合并所有批次
        result = torch.cat(all_embeddings, dim=0)

        if return_tensors == "np":
            return result.cpu().numpy()
        return result

    def batch_encode_documents(
        self,
        documents: List[str],
        batch_size: int = 32,
        return_tensors: str = "pt"
    ) -> Union[torch.Tensor, np.ndarray]:
        """
        批量编码文档（用于大规模文档）

        Args:
            documents: 文档列表
            batch_size: 批次大小
            return_tensors: 返回格式

        Returns:
            所有文档的 embeddings
        """
        all_embeddings = []

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_embs = self.encode_documents(batch, return_tensors="pt")
            all_embeddings.append(batch_embs)

        # 合并所有批次
        result = torch.cat(all_embeddings, dim=0)

        if return_tensors == "np":
            return result.cpu().numpy()
        return result

    def get_embedding_dim(self) -> int:
        """
        获取 embedding 维度

        Returns:
            embedding 向量的维度
        """
        test_text = ["test"]
        test_emb = self._encode(test_text)
        return test_emb.shape[1]

    def __repr__(self) -> str:
        return f"EmbeddingModel(model={self.model_name}, device={self.device})"


# 全局 embedding 模型实例（延迟加载）
_global_embedding_model: Optional[EmbeddingModel] = None


def get_embedding_model(
    model_name: str = "Qwen/Qwen3-Embedding-0.6B",
    device: str = "cuda",
    force_reload: bool = False,
    **kwargs
) -> EmbeddingModel:
    """
    获取全局 embedding 模型实例（单例模式）

    Args:
        model_name: 模型名称
        device: 设备类型
        force_reload: 是否强制重新加载
        **kwargs: 其他参数

    Returns:
        EmbeddingModel 实例
    """
    global _global_embedding_model

    if _global_embedding_model is None or force_reload:
        _global_embedding_model = EmbeddingModel(
            model_name=model_name,
            device=device,
            **kwargs
        )

    return _global_embedding_model


def encode_texts_for_chromadb(
    texts: List[str],
    is_query: bool = False,
    task_description: Optional[str] = None
) -> List[List[float]]:
    """
    为 ChromaDB 编码文本的便捷函数

    Args:
        texts: 文本列表
        is_query: 是否是查询（如果是，添加指令）
        task_description: 任务描述

    Returns:
        embeddings 列表（格式适配 ChromaDB）
    """
    model = get_embedding_model()

    if is_query:
        embeddings = model.encode_queries(
            texts,
            task_description=task_description or 'Given a web search query, retrieve relevant passages that answer the query',
            return_tensors="np"
        )
    else:
        embeddings = model.encode_documents(texts, return_tensors="np")

    # 转换为 ChromaDB 需要的格式
    return embeddings.tolist()
