#!/usr/bin/env python3
"""
测试本地模型路径是否可用

快速验证本地 Embedding 模型是否正确配置
"""

import sys
import os
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))


def check_model_files(model_path):
    """检查模型文件是否完整"""
    print(f"\n📂 检查模型目录: {model_path}")
    print("-" * 60)

    if not os.path.exists(model_path):
        print(f"❌ 路径不存在: {model_path}")
        return False

    if not os.path.isdir(model_path):
        print(f"❌ 不是目录: {model_path}")
        return False

    # 检查必要文件
    required_files = {
        "config.json": "模型配置文件",
        "tokenizer_config.json": "分词器配置",
    }

    # 至少需要一个模型权重文件
    weight_files = [
        "pytorch_model.bin",
        "model.safetensors",
        "pytorch_model.safetensors"
    ]

    print(f"✅ 目录存在")

    # 检查必需文件
    all_good = True
    for filename, description in required_files.items():
        filepath = os.path.join(model_path, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / 1024 / 1024
            print(f"✅ {filename} ({size_mb:.2f} MB) - {description}")
        else:
            print(f"❌ {filename} 缺失 - {description}")
            all_good = False

    # 检查权重文件
    found_weight = False
    for filename in weight_files:
        filepath = os.path.join(model_path, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / 1024 / 1024
            print(f"✅ {filename} ({size_mb:.2f} MB) - 模型权重")
            found_weight = True
            break

    if not found_weight:
        print(f"❌ 模型权重文件缺失 (需要以下之一: {', '.join(weight_files)})")
        all_good = False

    # 列出所有文件
    print(f"\n📋 目录中的所有文件:")
    try:
        files = os.listdir(model_path)
        for f in sorted(files)[:20]:  # 只显示前20个
            filepath = os.path.join(model_path, f)
            if os.path.isfile(filepath):
                size_mb = os.path.getsize(filepath) / 1024 / 1024
                print(f"  - {f} ({size_mb:.2f} MB)")
        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 个文件")
    except Exception as e:
        print(f"  ❌ 无法列出文件: {e}")

    return all_good


def test_vllm_model(model_path):
    """测试 vLLM 模型"""
    print(f"\n🧪 测试 vLLM 模型")
    print("=" * 60)

    try:
        import vllm
        print(f"✅ vllm 已安装: {vllm.__version__}")
    except ImportError:
        print("❌ vllm 未安装")
        print("   请运行: pip install vllm")
        return False

    try:
        from app.core.embedding_function import VLLMEmbeddingFunction

        print(f"\n正在加载模型...")
        embedding_fn = VLLMEmbeddingFunction(
            model_name_or_path=model_path,
            device="cuda"
        )

        print(f"✅ 模型加载成功")

        # 测试编码
        test_texts = ["测试文本", "向量数据库"]
        print(f"\n正在测试编码...")
        embeddings = embedding_fn(test_texts)

        print(f"✅ 编码成功")
        print(f"  - 文本数量: {len(test_texts)}")
        print(f"  - Embedding 数量: {len(embeddings)}")
        print(f"  - Embedding 维度: {len(embeddings[0])}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentence_transformers_model(model_path):
    """测试 SentenceTransformers 模型"""
    print(f"\n🧪 测试 SentenceTransformers 模型")
    print("=" * 60)

    try:
        import sentence_transformers
        print(f"✅ sentence-transformers 已安装: {sentence_transformers.__version__}")
    except ImportError:
        print("❌ sentence-transformers 未安装")
        print("   请运行: pip install sentence-transformers")
        return False

    try:
        from app.core.sentence_embedding_function import SentenceTransformerEmbeddingFunction

        print(f"\n正在加载模型...")
        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name_or_path=model_path
        )

        print(f"✅ 模型加载成功")

        # 测试编码
        test_texts = ["测试文本", "向量数据库"]
        print(f"\n正在测试编码...")
        embeddings = embedding_fn(test_texts)

        print(f"✅ 编码成功")
        print(f"  - 文本数量: {len(test_texts)}")
        print(f"  - Embedding 数量: {len(embeddings)}")
        print(f"  - Embedding 维度: {len(embeddings[0])}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("本地模型路径测试工具")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python test_local_model.py <模型路径> [vllm|st]")
        print("\n示例:")
        print("  python test_local_model.py /path/to/model vllm")
        print("  python test_local_model.py /path/to/model st")
        print("  python test_local_model.py /path/to/model  # 自动检测")
        sys.exit(1)

    model_path = sys.argv[1]
    model_type = sys.argv[2] if len(sys.argv) > 2 else None

    # 检查文件
    files_ok = check_model_files(model_path)

    if not files_ok:
        print("\n⚠️  模型文件不完整，但仍会尝试加载...")

    # 测试模型
    if model_type == "vllm":
        success = test_vllm_model(model_path)
    elif model_type == "st":
        success = test_sentence_transformers_model(model_path)
    else:
        print("\n自动检测模型类型...")
        print("尝试 SentenceTransformers...")
        success = test_sentence_transformers_model(model_path)

        if not success:
            print("\n尝试 vLLM...")
            success = test_vllm_model(model_path)

    # 总结
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！模型可以使用")
        print("\n💡 使用方法:")
        print(f"python migrate_vectordb.py --migrate \\")
        print(f"  --embedding-type {'vllm' if model_type == 'vllm' else 'sentence-transformers'} \\")
        print(f"  --model-path {model_path}")
    else:
        print("❌ 测试失败，请检查:")
        print("  1. 模型文件是否完整")
        print("  2. 依赖是否已安装 (vllm 或 sentence-transformers)")
        print("  3. 路径是否正确")
    print("=" * 60)


if __name__ == "__main__":
    main()
