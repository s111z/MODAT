#!/usr/bin/env python3
"""
测试 SentenceTransformers Embedding Function

验证 embedding 功能是否正常工作
"""

import sys
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def test_sentence_transformers():
    """测试 SentenceTransformers"""
    print("=" * 60)
    print("测试 SentenceTransformers Embedding Function")
    print("=" * 60)
    print()

    # 1. 检查依赖
    print("步骤 1: 检查依赖")
    print("-" * 60)
    try:
        import sentence_transformers
        print(f"✅ sentence-transformers 已安装: {sentence_transformers.__version__}")
    except ImportError:
        print("❌ sentence-transformers 未安装")
        print("   请运行: pip install sentence-transformers")
        return False

    # 2. 测试 Embedding Function
    print("\n步骤 2: 加载 Embedding Function")
    print("-" * 60)
    try:
        from app.core.sentence_embedding_function import SentenceTransformerEmbeddingFunction
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="moka-ai/m3e-base"
        )
        print("✅ Embedding Function 加载成功")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False

    # 3. 测试 Embedding 生成
    print("\n步骤 3: 测试 Embedding 生成")
    print("-" * 60)
    test_texts = [
        "人工智能的定义",
        "机器学习是人工智能的子领域",
        "深度学习模型训练"
    ]

    try:
        embeddings = embedding_fn(test_texts)
        print(f"✅ Embedding 生成成功")
        print(f"   - 文本数量: {len(test_texts)}")
        print(f"   - Embedding 数量: {len(embeddings)}")
        print(f"   - Embedding 维度: {len(embeddings[0])}")
    except Exception as e:
        print(f"❌ Embedding 生成失败: {e}")
        return False

    # 4. 测试相似度
    print("\n步骤 4: 测试语义相似度")
    print("-" * 60)
    import numpy as np

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    sim_01 = cosine_similarity(embeddings[0], embeddings[1])
    sim_02 = cosine_similarity(embeddings[0], embeddings[2])
    sim_12 = cosine_similarity(embeddings[1], embeddings[2])

    print(f"相似度矩阵:")
    print(f"  文本 0 vs 文本 1: {sim_01:.4f}")
    print(f"  文本 0 vs 文本 2: {sim_02:.4f}")
    print(f"  文本 1 vs 文本 2: {sim_12:.4f}")

    # 验证相似度合理性
    if 0 < sim_01 < 1 and 0 < sim_02 < 1 and 0 < sim_12 < 1:
        print("✅ 相似度计算正常")
    else:
        print("⚠️  相似度值异常")
        return False

    # 5. 测试 ChromaDB 集成
    print("\n步骤 5: 测试 ChromaDB 集成")
    print("-" * 60)
    try:
        import chromadb
        import tempfile
        import shutil

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"   使用临时目录: {temp_dir}")

        # 创建客户端和集合
        client = chromadb.PersistentClient(path=temp_dir)
        collection = client.create_collection(
            name="test_collection",
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        # 添加文档
        collection.add(
            ids=["id1", "id2", "id3"],
            documents=test_texts,
            metadatas=[
                {"source": "test1"},
                {"source": "test2"},
                {"source": "test3"}
            ]
        )
        print(f"✅ 文档添加成功: {collection.count()} 个")

        # 测试搜索
        results = collection.query(
            query_texts=["人工智能"],
            n_results=2
        )
        print(f"✅ 搜索成功: 找到 {len(results['ids'][0])} 个结果")

        # 清理
        shutil.rmtree(temp_dir)
        print(f"✅ ChromaDB 集成测试通过")

    except Exception as e:
        print(f"❌ ChromaDB 集成测试失败: {e}")
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    return True


def test_vllm():
    """测试 vLLM"""
    print("\n" + "=" * 60)
    print("测试 vLLM Embedding Function")
    print("=" * 60)
    print()

    # 检查依赖
    print("步骤 1: 检查依赖")
    print("-" * 60)
    try:
        import vllm
        print(f"✅ vllm 已安装: {vllm.__version__}")
    except ImportError:
        print("❌ vllm 未安装")
        print("   请运行: pip install vllm")
        return False

    # 测试 Embedding Function
    print("\n步骤 2: 加载 vLLM Embedding Function")
    print("-" * 60)
    try:
        from app.core.embedding_function import VLLMEmbeddingFunction
        embedding_fn = VLLMEmbeddingFunction(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            device="cuda"
        )
        print("✅ vLLM Embedding Function 加载成功")

        # 简单测试
        test_texts = ["测试文本"]
        embeddings = embedding_fn(test_texts)
        print(f"✅ Embedding 生成成功，维度: {len(embeddings[0])}")

        return True
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 Embedding 功能测试工具\n")

    # 测试 SentenceTransformers
    st_success = test_sentence_transformers()

    # 测试 vLLM（可选）
    print("\n" + "=" * 60)
    test_vllm_choice = input("是否测试 vLLM? (y/n): ").lower()
    if test_vllm_choice == 'y':
        vllm_success = test_vllm()
    else:
        print("⏭️  跳过 vLLM 测试")
        vllm_success = None

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"SentenceTransformers: {'✅ 通过' if st_success else '❌ 失败'}")
    if vllm_success is not None:
        print(f"vLLM: {'✅ 通过' if vllm_success else '❌ 失败'}")

    print("\n💡 推荐:")
    if st_success:
        print("   ✅ 可以使用 SentenceTransformers 进行迁移")
        print("   命令: python migrate_vectordb.py --migrate --embedding-type sentence-transformers")
    if vllm_success:
        print("   ✅ 可以使用 vLLM 进行迁移（推荐，效果最好）")
        print("   命令: python migrate_vectordb.py --migrate --embedding-type vllm")

    if not st_success and not vllm_success:
        print("   ⚠️  建议使用默认模型（临时）")
        print("   命令: python migrate_vectordb.py --migrate --embedding-type default")
