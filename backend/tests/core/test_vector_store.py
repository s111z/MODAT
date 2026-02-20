import pytest
from unittest.mock import MagicMock, patch, call
from app.core.vector_store import VectorDBManager


class TestVectorDBManager:
    """测试VectorDBManager类"""

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_init_default(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试默认初始化"""
        # 模拟集合
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        # 模拟客户端
        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()

        assert manager.client == mock_client_instance
        assert manager.collection == mock_collection
        mock_chroma_client.assert_called_once_with(path="./chroma_db")
        mock_client_instance.get_or_create_collection.assert_called_once()

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_init_with_custom_params(self, mock_embedding_fn, mock_chroma_client):
        """测试自定义参数初始化"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager(
            db_path="/custom/path",
            collection_name="custom_collection"
        )

        mock_chroma_client.assert_called_once_with(path="/custom/path")

        call_args = mock_client_instance.get_or_create_collection.call_args
        assert call_args[1]["name"] == "custom_collection"

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_add_texts_success(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试成功添加文本"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()

        texts = ["文本1", "文本2", "文本3"]
        result = manager.add_texts(texts)

        assert len(result) == 3
        mock_collection.upsert.assert_called_once()

        call_args = mock_collection.upsert.call_args
        assert call_args[1]["documents"] == texts
        assert len(call_args[1]["ids"]) == 3
        assert len(call_args[1]["metadatas"]) == 3

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_add_texts_with_metadata(self, mock_embedding_fn, mock_chroma_client):
        """测试添加带元数据的文本"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()

        texts = ["文本1", "文本2"]
        metadatas = [{"source": "file1.pdf"}, {"source": "file2.pdf"}]
        ids = ["id1", "id2"]

        result = manager.add_texts(texts, metadatas=metadatas, ids=ids)

        assert result == ids

        call_args = mock_collection.upsert.call_args
        assert call_args[1]["documents"] == texts
        assert call_args[1]["metadatas"] == metadatas
        assert call_args[1]["ids"] == ids

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_add_texts_empty_list(self, mock_embedding_fn, mock_chroma_client):
        """测试添加空列表"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        result = manager.add_texts([])

        assert result is None
        mock_collection.upsert.assert_not_called()

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_add_texts_exception(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试添加文本异常"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.upsert.side_effect = Exception("插入错误")

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        result = manager.add_texts(["文本"])

        assert result == []
        mock_print.assert_any_call("❌ [ChromaDB] 插入失败: 插入错误")

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_search_success(self, mock_embedding_fn, mock_chroma_client):
        """测试成功搜索"""
        mock_query_results = {
            "ids": [["id1", "id2"]],
            "documents": [["文档1", "文档2"]],
            "metadatas": [[{"source": "file1"}, {"source": "file2"}]],
            "distances": [[0.1, 0.2]]
        }

        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.query.return_value = mock_query_results

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        results = manager.search("测试查询", top_k=2)

        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["content"] == "文档1"
        assert results[0]["metadata"]["source"] == "file1"
        assert results[0]["distance"] == 0.1

        mock_collection.query.assert_called_once_with(
            query_texts=["测试查询"],
            n_results=2,
            where=None
        )

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_search_with_filter(self, mock_embedding_fn, mock_chroma_client):
        """测试带过滤条件的搜索"""
        mock_query_results = {
            "ids": [["id1"]],
            "documents": [["文档1"]],
            "metadatas": [[{"source": "file.pdf"}]],
            "distances": [[0.1]]
        }

        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.query.return_value = mock_query_results

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        filter_meta = {"source": "file.pdf"}
        results = manager.search("查询", top_k=3, filter_meta=filter_meta)

        mock_collection.query.assert_called_once_with(
            query_texts=["查询"],
            n_results=3,
            where=filter_meta
        )

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_search_exception(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试搜索异常"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.query.side_effect = Exception("查询错误")

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        results = manager.search("查询")

        assert results == []
        mock_print.assert_any_call("❌ [ChromaDB] 查询失败: 查询错误")

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_get_all(self, mock_embedding_fn, mock_chroma_client):
        """测试获取所有数据"""
        mock_get_results = {
            "ids": ["id1", "id2"],
            "documents": ["文档1", "文档2"],
            "metadatas": [{"source": "f1"}, {"source": "f2"}]
        }

        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.get.return_value = mock_get_results

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        results = manager.get_all(limit=5)

        assert len(results) == 2
        assert results[0]["id"] == "id1"
        assert results[0]["content"] == "文档1"
        assert results[1]["id"] == "id2"

        mock_collection.get.assert_called_once_with(limit=5)

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_update_text_success(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试成功更新文本"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        result = manager.update_text(
            "id1",
            "新文本",
            {"source": "new.pdf"}
        )

        assert result is True
        mock_collection.update.assert_called_once_with(
            ids=["id1"],
            documents=["新文本"],
            metadatas=[{"source": "new.pdf"}]
        )

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_update_text_without_metadata(self, mock_embedding_fn, mock_chroma_client):
        """测试不更新元数据"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        result = manager.update_text("id1", "新文本")

        assert result is True
        call_args = mock_collection.update.call_args
        assert call_args[1]["metadatas"] is None

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_update_text_exception(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试更新异常"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.update.side_effect = Exception("更新错误")

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        result = manager.update_text("id1", "文本")

        assert result is False
        mock_print.assert_any_call("❌ [ChromaDB] 更新失败: 更新错误")

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_delete_by_ids(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试根据ID删除"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        manager.delete_by_ids(["id1", "id2", "id3"])

        mock_collection.delete.assert_called_once_with(ids=["id1", "id2", "id3"])
        mock_print.assert_any_call("🗑️ [ChromaDB] 已删除 3 条数据")

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_delete_by_ids_exception(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试删除异常"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.delete.side_effect = Exception("删除错误")

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        manager.delete_by_ids(["id1"])

        mock_print.assert_any_call("❌ [ChromaDB] 删除失败: 删除错误")

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("builtins.print")
    def test_delete_by_filter(self, mock_print, mock_embedding_fn, mock_chroma_client):
        """测试根据过滤条件删除"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        filter_meta = {"source": "file.pdf"}
        manager.delete_by_filter(filter_meta)

        mock_collection.delete.assert_called_once_with(where=filter_meta)

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    def test_clean_results_empty(self, mock_embedding_fn, mock_chroma_client):
        """测试清洗空结果"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0

        mock_client_instance = MagicMock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.return_value = mock_client_instance

        manager = VectorDBManager()
        results = manager._clean_results({"ids": []})

        assert results == []

    @patch("app.core.vector_store.chromadb.PersistentClient")
    @patch("app.core.vector_store.embedding_functions.DefaultEmbeddingFunction")
    @patch("app.core.vector_store.VectorDBManager")
    def test_global_db_manager(self, mock_manager_class, mock_embedding_fn, mock_chroma_client):
        """测试全局db_manager实例"""
        from app.core.vector_store import db_manager
        assert db_manager is not None
