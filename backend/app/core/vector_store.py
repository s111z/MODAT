import chromadb
import uuid
import logging
from typing import List, Dict, Optional, Any

_logger = logging.getLogger("vector_store")


def _create_embedding_function(settings):
    """Create the configured ChromaDB embedding function."""
    embedding_type = settings.embedding_model_type.lower()

    if embedding_type in {"sentence-transformers", "sentence_transformers", "st"}:
        from .sentence_embedding_function import create_embedding_function

        _logger.info(
            "[ChromaDB] 使用 SentenceTransformers Embedding: %s (%s)",
            settings.embedding_model_name,
            settings.embedding_device,
        )
        return create_embedding_function(
            model_key=settings.embedding_model_name,
            device=settings.embedding_device,
        )

    if embedding_type == "default":
        from chromadb.utils import embedding_functions

        _logger.warning("[ChromaDB] 使用默认 Embedding 模型，对中文支持一般")
        return embedding_functions.DefaultEmbeddingFunction()

    if embedding_type == "openai":
        import os
        from chromadb.utils import embedding_functions

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("使用 OpenAI embedding 需要设置 OPENAI_API_KEY 环境变量")
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        )

    from .embedding_function import VLLMEmbeddingFunction
    import os

    model_path = os.path.join(settings.model_base_dir, settings.embedding_model_name)
    _logger.info("[ChromaDB] 使用 vLLM Embedding 模型: %s", model_path)
    return VLLMEmbeddingFunction(
        model_name_or_path=settings.embedding_model_name,
        device=settings.embedding_device,
    )


class VectorDBManager:
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "mota_knowledge"):
        """
        初始化 ChromaDB 客户端。
        :param db_path: 数据持久化路径
        :param collection_name: 集合名称
        """
        # 1. 初始化持久化客户端
        self.client = chromadb.PersistentClient(path=db_path)

        # 2. 设置嵌入模型
        from .config import settings
        self.embedding_fn = _create_embedding_function(settings)

        # 3. 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        _logger.info("[ChromaDB] 已加载集合: %s, 当前数据量: %d",
                     collection_name, self.collection.count())

    # ==========================
    # C (Create) - 增 / 插入
    # ==========================
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None):
        """
        批量添加文本到向量数据库。
        """
        if not texts:
            return
        
        count = len(texts)
        ids = []
        for item in metadatas:
            ids.append(item["file_id"])

        try:
            # 使用 upsert：如果 ID 存在则更新，不存在则插入
            self.collection.upsert(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ [ChromaDB] 成功存入 {count} 条数据")
            return ids
        except Exception as e:
            print(f"❌ [ChromaDB] 插入失败: {e}")
            return []

    # ==========================
    # R (Read) - 查 / 搜索
    # ==========================
    def search(self, query: str, top_k: int = 3, filter_meta: Optional[Dict] = None) -> List[Dict]:
        """
        语义搜索。
        :param filter_meta: 过滤条件，例如 {"source": "file.pdf"}
        """
        try:
            count = self.collection.count()
            actual_k = min(top_k, count)
            if actual_k == 0:
                _logger.warning("[ChromaDB] 集合为空，无法检索")
                return []
            results = self.collection.query(
                query_texts=[query],
                n_results=actual_k,
                where=filter_meta
            )
            cleaned = self._clean_results(results)
            _logger.debug("[ChromaDB] query=%s top_k=%d 集合总量=%d 命中=%d",
                          query[:40], top_k, count, len(cleaned))
            return cleaned
        except Exception as e:
            _logger.error("[ChromaDB] 查询失败: %s", e)
            return []

    def get_all(self, limit: int = 10) -> List[Dict]:
        """获取前 N 条数据（用于调试）"""
        results = self.collection.get(limit=limit)
        # 构造伪 query 结构
        data = []
        if results['ids']:
            for i in range(len(results['ids'])):
                data.append({
                    "id": results['ids'][i],
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })
        return data

    def get_all_sources(self) -> set:
        """获取向量库中所有已入库文件的 source 路径（去重）"""
        try:
            total = self.collection.count()
            if total == 0:
                return set()
            results = self.collection.get(
                limit=total,
                include=["metadatas"]
            )
            sources = set()
            if results['metadatas']:
                for meta in results['metadatas']:
                    if meta and meta.get("source"):
                        sources.add(meta["source"])
            return sources
        except Exception as e:
            print(f"❌ [ChromaDB] 获取已入库源失败: {e}")
            return set()

    # ==========================
    # U (Update) - 改 / 更新
    # ==========================
    def update_text(self, doc_id: str, new_text: str, new_metadata: Optional[Dict] = None):
        """
        根据 ID 更新单条数据。
        """
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[new_text],
                metadatas=[new_metadata] if new_metadata else None
            )
            print(f"✅ [ChromaDB] ID {doc_id} 更新成功")
            return True
        except Exception as e:
            print(f"❌ [ChromaDB] 更新失败: {e}")
            return False

    # ==========================
    # D (Delete) - 删 / 删除
    # ==========================
    def delete_by_ids(self, ids: List[str]):
        """根据 ID 列表删除"""
        try:
            self.collection.delete(ids=ids)
            print(f"🗑️ [ChromaDB] 已删除 {len(ids)} 条数据")
        except Exception as e:
            print(f"❌ [ChromaDB] 删除失败: {e}")

    def delete_by_filter(self, filter_meta: Dict):
        """
        根据条件删除。
        例如：删除某个文件的所有切片 -> delete_by_filter({"source": "report.pdf"})
        """
        try:
            self.collection.delete(where=filter_meta)
            print(f"🗑️ [ChromaDB] 已根据过滤条件删除数据")
        except Exception as e:
            print(f"❌ [ChromaDB] 删除失败: {e}")

    # ==========================
    # Helper - 数据清洗
    # ==========================
    def _clean_results(self, results: Dict) -> List[Dict]:
        """
        将 Chroma 复杂的返回结构转换为扁平的 List[Dict]
        """
        cleaned = []
        if not results['ids']:
            return cleaned
            
        # results['ids'] 是一个二维列表 [[id1, id2...]] 因为 query 支持批量查询
        for i in range(len(results['ids'][0])):
            cleaned.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
        return cleaned

# 初始化全局单例
db_manager = VectorDBManager()
