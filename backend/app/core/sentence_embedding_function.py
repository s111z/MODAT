"""
SentenceTransformer Embedding Function for ChromaDB

使用 SentenceTransformers 作为 vLLM 的备选方案
适合 GPU 显存不足或无法安装 vLLM 的场景
"""

from typing import List
from chromadb import EmbeddingFunction, Embeddings
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    """
    使用 SentenceTransformer 的 Embedding Function

    支持多种中文优化模型：
    - moka-ai/m3e-base: 768维，中文优化
    - BAAI/bge-small-zh-v1.5: 512维，中文，轻量级
    - shibing624/text2vec-base-chinese: 768维，中文
    """

    def __init__(
        self,
        model_name_or_path: str = "moka-ai/m3e-base",
        device: str = None,
        normalize_embeddings: bool = True
    ):
        """
        初始化 SentenceTransformer Embedding Function

        Args:
            model_name_or_path: 模型名称（HuggingFace）或本地路径
                - HuggingFace: "moka-ai/m3e-base"
                - 本地路径: "/path/to/local/model"
            device: 设备 ("cuda", "cpu" 或 None 自动选择)
            normalize_embeddings: 是否归一化 embedding（推荐 True）
        """
        self.model_name = model_name_or_path
        self.normalize_embeddings = normalize_embeddings

        import os
        if os.path.exists(model_name_or_path):
            logger.info(f"正在从本地路径加载 SentenceTransformer 模型: {model_name_or_path}")
        else:
            logger.info(f"正在从 HuggingFace 加载 SentenceTransformer 模型: {model_name_or_path}")

        try:
            self.model = SentenceTransformer(model_name_or_path, device=device)
            logger.info(f"✅ 模型加载成功，维度: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def __call__(self, input: List[str]) -> Embeddings:
        """
        执行 embedding

        Args:
            input: 输入文本列表

        Returns:
            Embeddings: embedding 向量列表
        """
        embeddings = self.model.encode(
            input,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        return embeddings.tolist()


# 推荐的中文模型配置
RECOMMENDED_MODELS = {
    "m3e-base": {
        "name": "moka-ai/m3e-base",
        "dimension": 768,
        "description": "M3E 基础模型，中文优化，平衡性能和效果"
    },
    "bge-small-zh": {
        "name": "BAAI/bge-small-zh-v1.5",
        "dimension": 512,
        "description": "BGE 小型中文模型，轻量级，速度快"
    },
    "bge-base-zh": {
        "name": "BAAI/bge-base-zh-v1.5",
        "dimension": 768,
        "description": "BGE 基础中文模型，效果好"
    },
    "bge-large-zh": {
        "name": "BAAI/bge-large-zh-v1.5",
        "dimension": 1024,
        "description": "BGE 大型中文模型，效果最好但速度慢"
    },
    "text2vec": {
        "name": "shibing624/text2vec-base-chinese",
        "dimension": 768,
        "description": "Text2Vec 中文模型"
    }
}


def create_embedding_function(model_key: str = "m3e-base", device: str = None, model_path: str = None):
    """
    便捷函数：创建 embedding function

    Args:
        model_key: 模型键名（见 RECOMMENDED_MODELS）或自定义模型名
        device: 设备
        model_path: 本地模型路径（优先级高于 model_key）

    Returns:
        SentenceTransformerEmbeddingFunction

    Examples:
        # 使用预设模型
        create_embedding_function("m3e-base")

        # 使用本地模型
        create_embedding_function(model_path="/path/to/local/model")

        # 使用 HuggingFace 模型名
        create_embedding_function("BAAI/bge-base-zh-v1.5")
    """
    if model_path:
        # 优先使用本地路径
        model_name = model_path
    elif model_key in RECOMMENDED_MODELS:
        model_name = RECOMMENDED_MODELS[model_key]["name"]
    else:
        model_name = model_key  # 直接使用提供的名称

    return SentenceTransformerEmbeddingFunction(
        model_name_or_path=model_name,
        device=device
    )


# 使用示例
if __name__ == "__main__":
    # 测试 embedding function
    print("测试 SentenceTransformer Embedding Function\n")

    # 创建 embedding function
    embedding_fn = create_embedding_function("m3e-base")

    # 测试文本
    texts = [
        "人工智能的定义是什么？",
        "机器学习是人工智能的一个分支",
        "深度学习模型需要大量数据训练"
    ]

    # 生成 embeddings
    print(f"测试文本数: {len(texts)}")
    embeddings = embedding_fn(texts)

    print(f"\nEmbedding 结果:")
    print(f"- 数量: {len(embeddings)}")
    print(f"- 维度: {len(embeddings[0])}")
    print(f"- 第一个向量前 10 维: {embeddings[0][:10]}")

    # 计算相似度
    import numpy as np

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    print(f"\n相似度测试:")
    print(f"文本 0 vs 文本 1: {cosine_similarity(embeddings[0], embeddings[1]):.4f}")
    print(f"文本 0 vs 文本 2: {cosine_similarity(embeddings[0], embeddings[2]):.4f}")
    print(f"文本 1 vs 文本 2: {cosine_similarity(embeddings[1], embeddings[2]):.4f}")

    print("\n✅ 测试完成")
