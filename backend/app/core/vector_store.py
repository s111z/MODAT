import chromadb
import uuid
from typing import List, Dict, Optional, Any
# from chromadb.utils import embedding_functions
from embedding_function import VLLMEmbeddingFunction

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
        # 注意：默认的 all-MiniLM-L6-v2 对中文支持一般。
        # 生产环境建议换成 OpenAIEmbeddingFunction 或 HuggingFace 的中文模型。
        self.embedding_fn = VLLMEmbeddingFunction()
        
        # 3. 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"} # 使用余弦相似度
        )
        print(f"📦 [ChromaDB] 已加载集合: {collection_name}, 当前数据量: {self.collection.count()}")

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
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_meta # Chroma 的过滤语法
            )
            return self._clean_results(results)
        except Exception as e:
            print(f"❌ [ChromaDB] 查询失败: {e}")
            return []

    def get_all(self, limit: int = 10) -> List[Dict]:
        """获取前 N 条数据（用于调试）"""
        results = self.collection.get(limit=limit)
        # 构造伪 query 结果结构以便复用清洗逻辑
        # 注意：get 返回的结构和 query 略有不同，这里简单处理
        data = []
        if results['ids']:
            for i in range(len(results['ids'])):
                data.append({
                    "id": results['ids'][i],
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })
        return data

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