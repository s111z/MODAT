import pytest
from unittest.mock import MagicMock, patch, Mock
import torch
import numpy as np


class TestEmbeddingModel:
    """测试 EmbeddingModel 类"""

    @patch('app.core.embedding.LLM')
    def test_init_success(self, mock_llm):
        """测试成功初始化"""
        from app.core.embedding import EmbeddingModel

        model = EmbeddingModel(
            model_name="test_model",
            device="cpu"
        )

        assert model.model_name == "test_model"
        assert model.device == "cpu"
        mock_llm.assert_called_once()

    def test_get_detailed_instruct(self):
        """测试指令格式化"""
        from app.core.embedding import EmbeddingModel

        with patch('app.core.embedding.LLM'):
            model = EmbeddingModel()

            result = model.get_detailed_instruct("task description", "query text")

            assert result == "Instruct: task description\nQuery: query text"

    @patch('app.core.embedding.LLM')
    def test_encode_queries_single(self, mock_llm):
        """测试编码单个查询"""
        from app.core.embedding import EmbeddingModel

        # Mock 模型输出
        mock_output = Mock()
        mock_output.outputs.embedding = [0.1, 0.2, 0.3]

        mock_llm_instance = Mock()
        mock_llm_instance.embed.return_value = [mock_output]
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        result = model.encode_queries("test query")

        assert isinstance(result, torch.Tensor)
        assert result.shape[0] == 1  # 一个查询

    @patch('app.core.embedding.LLM')
    def test_encode_queries_multiple(self, mock_llm):
        """测试编码多个查询"""
        from app.core.embedding import EmbeddingModel

        # Mock 模型输出
        mock_outputs = [Mock(), Mock()]
        for mock_output in mock_outputs:
            mock_output.outputs.embedding = [0.1, 0.2, 0.3]

        mock_llm_instance = Mock()
        mock_llm_instance.embed.return_value = mock_outputs
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        result = model.encode_queries(["query1", "query2"])

        assert isinstance(result, torch.Tensor)
        assert result.shape[0] == 2  # 两个查询

    @patch('app.core.embedding.LLM')
    def test_encode_documents(self, mock_llm):
        """测试编码文档"""
        from app.core.embedding import EmbeddingModel

        mock_output = Mock()
        mock_output.outputs.embedding = [0.1, 0.2, 0.3]

        mock_llm_instance = Mock()
        mock_llm_instance.embed.return_value = [mock_output]
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        result = model.encode_documents("test document")

        assert isinstance(result, torch.Tensor)
        assert result.shape[0] == 1

    @patch('app.core.embedding.LLM')
    def test_encode_with_instruction(self, mock_llm):
        """测试带指令的编码"""
        from app.core.embedding import EmbeddingModel

        mock_output = Mock()
        mock_output.outputs.embedding = [0.1, 0.2, 0.3]

        mock_llm_instance = Mock()
        mock_llm_instance.embed.return_value = [mock_output]
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        result = model.encode("test text", add_instruction=True)

        assert isinstance(result, torch.Tensor)

    @patch('app.core.embedding.LLM')
    def test_compute_similarity(self, mock_llm):
        """测试相似度计算"""
        from app.core.embedding import EmbeddingModel

        mock_llm_instance = Mock()
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()

        # 创建测试数据
        query_embs = torch.tensor([[1.0, 0.0, 0.0]])
        doc_embs = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

        scores = model.compute_similarity(query_embs, doc_embs)

        assert scores.shape == (1, 2)  # 1个查询 x 2个文档

    @patch('app.core.embedding.LLM')
    def test_search(self, mock_llm):
        """测试搜索功能"""
        from app.core.embedding import EmbeddingModel

        # Mock embeddings
        mock_outputs = [
            Mock(),  # query
            Mock(),  # doc1
            Mock()   # doc2
        ]
        mock_outputs[0].outputs.embedding = [1.0, 0.0, 0.0]
        mock_outputs[1].outputs.embedding = [1.0, 0.0, 0.0]
        mock_outputs[2].outputs.embedding = [0.0, 1.0, 0.0]

        mock_llm_instance = Mock()

        def mock_embed(texts):
            if len(texts) == 1:  # query
                return [mock_outputs[0]]
            else:  # documents
                return mock_outputs[1:]

        mock_llm_instance.embed.side_effect = mock_embed
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        results = model.search(
            "test query",
            ["doc1", "doc2"],
            top_k=2
        )

        assert len(results) <= 2
        assert all(len(item) == 3 for item in results)  # (index, score, content)

    @patch('app.core.embedding.LLM')
    def test_return_numpy(self, mock_llm):
        """测试返回 NumPy 格式"""
        from app.core.embedding import EmbeddingModel

        mock_output = Mock()
        mock_output.outputs.embedding = [0.1, 0.2, 0.3]

        mock_llm_instance = Mock()
        mock_llm_instance.embed.return_value = [mock_output]
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        result = model.encode_documents("test", return_tensors="np")

        assert isinstance(result, np.ndarray)

    @patch('app.core.embedding.LLM')
    def test_batch_encode_queries(self, mock_llm):
        """测试批量编码查询"""
        from app.core.embedding import EmbeddingModel

        mock_outputs = [Mock() for _ in range(5)]
        for mock_output in mock_outputs:
            mock_output.outputs.embedding = [0.1, 0.2, 0.3]

        mock_llm_instance = Mock()
        mock_llm_instance.embed.return_value = mock_outputs
        mock_llm.return_value = mock_llm_instance

        model = EmbeddingModel()
        queries = [f"query{i}" for i in range(5)]
        result = model.batch_encode_queries(queries, batch_size=2)

        assert isinstance(result, torch.Tensor)
        assert result.shape[0] == 5


class TestEmbeddingFunctions:
    """测试便捷函数"""

    @patch('app.core.embedding.EmbeddingModel')
    def test_get_embedding_model_singleton(self, mock_model_class):
        """测试单例模式"""
        from app.core.embedding import get_embedding_model, _global_embedding_model

        # 清除全局实例
        import app.core.embedding as emb_module
        emb_module._global_embedding_model = None

        mock_instance = Mock()
        mock_model_class.return_value = mock_instance

        # 第一次调用
        model1 = get_embedding_model()
        # 第二次调用（应该返回同一个实例）
        model2 = get_embedding_model()

        assert model1 is model2
        mock_model_class.assert_called_once()  # 只创建一次

    @patch('app.core.embedding.get_embedding_model')
    def test_encode_texts_for_chromadb_query(self, mock_get_model):
        """测试为 ChromaDB 编码查询"""
        from app.core.embedding import encode_texts_for_chromadb

        mock_model = Mock()
        mock_model.encode_queries.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_get_model.return_value = mock_model

        result = encode_texts_for_chromadb(["test query"], is_query=True)

        assert isinstance(result, list)
        assert isinstance(result[0], list)
        mock_model.encode_queries.assert_called_once()

    @patch('app.core.embedding.get_embedding_model')
    def test_encode_texts_for_chromadb_document(self, mock_get_model):
        """测试为 ChromaDB 编码文档"""
        from app.core.embedding import encode_texts_for_chromadb

        mock_model = Mock()
        mock_model.encode_documents.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_get_model.return_value = mock_model

        result = encode_texts_for_chromadb(["test doc"], is_query=False)

        assert isinstance(result, list)
        mock_model.encode_documents.assert_called_once()


class TestVLLMEmbeddingFunction:
    """测试 ChromaDB Embedding Function"""

    @patch('app.core.embedding_function.get_embedding_model')
    def test_embedding_function_call(self, mock_get_model):
        """测试 Embedding Function 调用"""
        from app.core.embedding_function import VLLMEmbeddingFunction

        mock_model = Mock()
        mock_model.encode_documents.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_get_model.return_value = mock_model

        emb_fn = VLLMEmbeddingFunction()
        result = emb_fn(["doc1", "doc2"])

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], list)

    @patch('app.core.embedding_function.get_embedding_model')
    def test_query_embedding_function(self, mock_get_model):
        """测试查询 Embedding Function"""
        from app.core.embedding_function import VLLMQueryEmbeddingFunction

        mock_model = Mock()
        mock_model.encode_queries.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_get_model.return_value = mock_model

        query_fn = VLLMQueryEmbeddingFunction()
        result = query_fn.embed_query("test query")

        assert isinstance(result, list)
        assert len(result) == 3  # embedding dim


class TestVectorDBConfig:
    """测试向量数据库配置"""

    @patch.dict('os.environ', {'EMBEDDING_MODEL_TYPE': 'default'})
    def test_get_embedding_function_default(self):
        """测试获取默认 embedding function"""
        from app.core.vector_db_config import get_embedding_function

        emb_fn = get_embedding_function()
        assert emb_fn is not None

    @patch.dict('os.environ', {'EMBEDDING_MODEL_TYPE': 'vllm'})
    @patch('app.core.vector_db_config.VLLMEmbeddingFunction')
    def test_get_embedding_function_vllm(self, mock_vllm_fn):
        """测试获取 vllm embedding function"""
        from app.core.vector_db_config import get_embedding_function

        mock_instance = Mock()
        mock_vllm_fn.return_value = mock_instance

        emb_fn = get_embedding_function()

        assert emb_fn is mock_instance
        mock_vllm_fn.assert_called_once()
