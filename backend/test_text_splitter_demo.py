#!/usr/bin/env python3
"""
文档切分功能测试脚本

演示如何使用文档切分器和node_parse_doc节点
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    split_text_by_characters,
    split_text_recursive
)


def demo_basic_splitting():
    """演示基本的文本切分"""
    print("=" * 60)
    print("示例1: 基本文本切分")
    print("=" * 60)

    text = """人工智能（Artificial Intelligence），英文缩写为AI。它是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。

人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器，该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。

自从人工智能诞生以来，理论和技术日益成熟，应用领域也不断扩大，可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。"""

    # 使用字符切分器
    splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20, separator="\n")
    chunks = splitter.split_text(text)

    print(f"\n原文长度: {len(text)} 字符")
    print(f"切分结果: {len(chunks)} 个chunks\n")

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1} ({len(chunk)} 字符):")
        print(f"  {chunk[:50]}..." if len(chunk) > 50 else f"  {chunk}")
        print()


def demo_recursive_splitting():
    """演示递归切分"""
    print("=" * 60)
    print("示例2: 递归文本切分（推荐）")
    print("=" * 60)

    text = """第一章 引言

人工智能的发展历史可以追溯到20世纪50年代。当时，计算机科学家开始探索机器能否模拟人类智能。

第二章 核心技术

人工智能的核心技术包括：
- 机器学习
- 深度学习
- 自然语言处理
- 计算机视觉

第三章 应用领域

人工智能已经在多个领域得到应用：
1. 医疗诊断
2. 金融分析
3. 自动驾驶
4. 智能客服"""

    # 使用递归切分器
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=30,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(text)

    print(f"\n原文长度: {len(text)} 字符")
    print(f"切分结果: {len(chunks)} 个chunks\n")

    for i, chunk in enumerate(chunks):
        print(f"Chunk {i + 1} ({len(chunk)} 字符):")
        print("-" * 50)
        print(chunk)
        print()


def demo_with_metadata():
    """演示带元数据的切分"""
    print("=" * 60)
    print("示例3: 带元数据的切分")
    print("=" * 60)

    text = "人工智能技术正在快速发展。" * 20

    splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=20)

    metadata = {
        "source": "ai_article.txt",
        "author": "张三",
        "created_at": "2024-01-01"
    }

    chunks_with_meta = splitter.create_chunks_with_metadata(text, metadata)

    print(f"\n原文长度: {len(text)} 字符")
    print(f"切分结果: {len(chunks_with_meta)} 个chunks\n")

    for item in chunks_with_meta:
        print(f"Chunk {item['metadata']['chunk_index'] + 1}:")
        print(f"  文本: {item['text'][:40]}...")
        print(f"  元数据: {item['metadata']}")
        print()


def demo_convenience_functions():
    """演示便捷函数"""
    print("=" * 60)
    print("示例4: 使用便捷函数")
    print("=" * 60)

    text = "这是一个测试文本。" * 30

    # 快速切分
    chunks1 = split_text_by_characters(text, chunk_size=100, chunk_overlap=20)
    print(f"\n按字符切分: {len(chunks1)} 个chunks")

    chunks2 = split_text_recursive(text, chunk_size=100, chunk_overlap=20)
    print(f"递归切分: {len(chunks2)} 个chunks")


def demo_node_parse_doc():
    """演示 node_parse_doc 节点"""
    print("=" * 60)
    print("示例5: 使用 node_parse_doc 节点")
    print("=" * 60)

    try:
        from app.graph.vectordb_nodes import node_parse_doc

        # 创建一个测试文本文件
        test_file = "test_document.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("人工智能（AI）是计算机科学的一个分支。\n\n" * 10)

        # 准备状态
        state = {
            "filename": test_file,
            "file_type": "txt",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "file_id": "test_001",
            "source": test_file,
            "category": "测试",
            "permissions": 1,
            "steps": [],
            "success": False,
            "message": "",
            "results": []
        }

        print("\n执行 node_parse_doc 节点...")
        result = node_parse_doc(state)

        print(f"\n执行结果:")
        print(f"  成功: {result['success']}")
        print(f"  消息: {result['message']}")
        print(f"\n执行步骤:")
        for step in result['steps']:
            print(f"  - {step}")

        if result['success'] and result['results']:
            print(f"\n详细结果:")
            for key, value in result['results'][0].items():
                print(f"  {key}: {value}")

        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n已清理测试文件: {test_file}")

    except ImportError as e:
        print(f"\n❌ 无法导入模块: {e}")
        print("请确保在 backend 目录下运行此脚本")
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")


def main():
    """主函数"""
    print("\n🚀 文档切分功能演示")
    print("=" * 60)

    demos = [
        ("基本切分", demo_basic_splitting),
        ("递归切分", demo_recursive_splitting),
        ("带元数据", demo_with_metadata),
        ("便捷函数", demo_convenience_functions),
        ("节点使用", demo_node_parse_doc)
    ]

    if len(sys.argv) > 1:
        # 运行特定示例
        demo_num = int(sys.argv[1])
        if 1 <= demo_num <= len(demos):
            name, func = demos[demo_num - 1]
            print(f"\n运行示例 {demo_num}: {name}\n")
            func()
        else:
            print(f"错误: 示例编号必须在 1-{len(demos)} 之间")
    else:
        # 运行所有示例
        print("\n运行所有示例...\n")
        for i, (name, func) in enumerate(demos, 1):
            try:
                func()
                input(f"\n按回车键继续到下一个示例... (示例 {i}/{len(demos)})\n")
            except KeyboardInterrupt:
                print("\n\n用户中断")
                break
            except Exception as e:
                print(f"\n❌ 示例 {i} 执行出错: {e}")
                continue

    print("\n" + "=" * 60)
    print("✨ 演示完成!")
    print("=" * 60)
    print("\n使用方法:")
    print("  python test_text_splitter_demo.py        # 运行所有示例")
    print("  python test_text_splitter_demo.py 1      # 运行示例1")
    print("  python test_text_splitter_demo.py 5      # 运行示例5")
    print()


if __name__ == "__main__":
    main()
