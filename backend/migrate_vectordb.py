#!/usr/bin/env python3
"""
向量数据库迁移工具

用于在更换 embedding 模型时迁移数据
支持备份、导出、重建和验证功能
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions

# 添加项目路径
current_file_path = Path(__file__).resolve()
BASE_DIR = current_file_path.parent
sys.path.insert(0, str(BASE_DIR))

# 配置
DEFAULT_DB_PATH = "./chroma_db"
DEFAULT_COLLECTION = "mota_knowledge"
BACKUP_DIR = "./chroma_db_backups"
EXPORT_DIR = "./vectordb_exports"


class VectorDBMigrator:
    """向量数据库迁移器"""

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION
    ):
        self.db_path = db_path
        self.collection_name = collection_name
        self.backup_dir = BACKUP_DIR
        self.export_dir = EXPORT_DIR

        # 创建必要的目录
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)

    def get_status(self) -> Dict[str, Any]:
        """获取当前数据库状态"""
        print("🔍 正在检查数据库状态...")

        if not os.path.exists(self.db_path):
            return {
                "exists": False,
                "message": "数据库不存在"
            }

        try:
            client = chromadb.PersistentClient(path=self.db_path)
            collection = client.get_collection(name=self.collection_name)

            count = collection.count()
            # 获取样本数据
            sample = collection.get(limit=1)

            # 检测 embedding 维度
            embedding_dim = None
            if sample['embeddings'] and len(sample['embeddings']) > 0:
                embedding_dim = len(sample['embeddings'][0])

            status = {
                "exists": True,
                "db_path": self.db_path,
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_dimension": embedding_dim,
                "sample_metadata": sample['metadatas'][0] if sample['metadatas'] else None
            }

            print("\n✅ 数据库状态:")
            print(f"  - 路径: {status['db_path']}")
            print(f"  - 集合名称: {status['collection_name']}")
            print(f"  - 文档数量: {status['document_count']}")
            print(f"  - Embedding 维度: {status['embedding_dimension']}")

            return status

        except Exception as e:
            return {
                "exists": True,
                "error": str(e),
                "message": f"读取数据库失败: {e}"
            }

    def backup(self) -> str:
        """备份当前数据库"""
        print("\n💾 正在备份数据库...")

        if not os.path.exists(self.db_path):
            print("❌ 数据库不存在，无需备份")
            return None

        # 生成备份名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)

        try:
            # 复制整个数据库目录
            shutil.copytree(self.db_path, backup_path)

            # 保存备份信息
            info = {
                "timestamp": timestamp,
                "source_path": self.db_path,
                "backup_path": backup_path,
                "collection_name": self.collection_name
            }

            info_file = os.path.join(backup_path, "backup_info.json")
            with open(info_file, "w") as f:
                json.dump(info, f, indent=2)

            size_mb = sum(f.stat().st_size for f in Path(backup_path).rglob('*')) / 1024 / 1024

            print(f"✅ 备份完成:")
            print(f"  - 备份路径: {backup_path}")
            print(f"  - 备份大小: {size_mb:.2f} MB")

            return backup_path

        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return None

    def export_data(self) -> str:
        """导出数据为JSON格式"""
        print("\n📤 正在导出数据...")

        if not os.path.exists(self.db_path):
            print("❌ 数据库不存在")
            return None

        try:
            client = chromadb.PersistentClient(path=self.db_path)
            collection = client.get_collection(name=self.collection_name)

            # 获取所有数据
            all_data = collection.get()

            # 准备导出数据
            export_data = {
                "collection_name": self.collection_name,
                "export_time": datetime.now().isoformat(),
                "document_count": len(all_data['ids']),
                "documents": []
            }

            # 组织数据
            for i in range(len(all_data['ids'])):
                doc = {
                    "id": all_data['ids'][i],
                    "text": all_data['documents'][i],
                    "metadata": all_data['metadatas'][i] if all_data['metadatas'] else None
                }
                export_data['documents'].append(doc)

            # 保存为JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = os.path.join(self.export_dir, f"export_{timestamp}.json")

            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            file_size = os.path.getsize(export_file) / 1024 / 1024

            print(f"✅ 导出完成:")
            print(f"  - 导出文件: {export_file}")
            print(f"  - 文档数量: {export_data['document_count']}")
            print(f"  - 文件大小: {file_size:.2f} MB")

            return export_file

        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return None

    def migrate(
        self,
        embedding_type: str = "vllm",
        new_collection: str = None,
        batch_size: int = 100,
        model_path: str = None
    ) -> bool:
        """
        迁移数据到新的 embedding 模型

        Args:
            embedding_type: 新的 embedding 类型 (vllm, sentence-transformers, default, openai)
            new_collection: 新集合名称（None表示使用原名称）
            batch_size: 批处理大小
            model_path: 本地模型路径（可选，用于 vllm 和 sentence-transformers）
        """
        print("\n🔄 开始迁移...")

        # 1. 备份
        print("\n步骤 1/5: 备份当前数据库")
        backup_path = self.backup()
        if not backup_path:
            print("❌ 备份失败，终止迁移")
            return False

        # 2. 导出数据
        print("\n步骤 2/5: 导出现有数据")
        export_file = self.export_data()
        if not export_file:
            print("❌ 导出失败，终止迁移")
            return False

        # 加载导出的数据
        with open(export_file, "r", encoding="utf-8") as f:
            exported_data = json.load(f)

        documents = exported_data['documents']
        total_docs = len(documents)

        print(f"  - 待迁移文档: {total_docs} 个")

        # 3. 创建新数据库
        print("\n步骤 3/5: 创建新数据库")

        # 备份旧数据库并删除
        old_db_backup = f"{self.db_path}_old"
        if os.path.exists(self.db_path):
            # 先删除旧的备份（如果存在）
            if os.path.exists(old_db_backup):
                print(f"  - 删除已存在的旧备份: {old_db_backup}")
                shutil.rmtree(old_db_backup)

            # 移动当前数据库
            shutil.move(self.db_path, old_db_backup)
            print(f"  - 旧数据库已移至: {old_db_backup}")

        # 确保目标路径不存在（多次检查）
        import time
        for attempt in range(3):
            if os.path.exists(self.db_path):
                print(f"  - 清理残留数据库目录: {self.db_path} (尝试 {attempt + 1}/3)")
                try:
                    shutil.rmtree(self.db_path)
                    time.sleep(0.5)  # 等待文件系统同步
                except Exception as e:
                    print(f"    警告: 清理失败 - {e}")
                    if attempt == 2:
                        print(f"    ❌ 无法清理目录，请手动删除: rm -rf {self.db_path}")
                        return False
            else:
                break

        # 最终确认目录不存在
        if os.path.exists(self.db_path):
            print(f"  ❌ 错误: {self.db_path} 仍然存在，无法继续")
            print(f"  请手动删除: rm -rf {self.db_path}")
            return False

        print(f"  ✅ 旧数据库清理完成")

        # 设置新的 embedding function
        if embedding_type == "vllm":
            model_name_or_path = model_path or "Qwen/Qwen3-Embedding-0.6B"
            print(f"  - 使用 vllm embedding")
            print(f"    模型: {model_name_or_path}")
            try:
                from app.core.embedding_function import VLLMEmbeddingFunction
                embedding_fn = VLLMEmbeddingFunction(
                    model_name_or_path=model_name_or_path,
                    device="cuda"
                )
                print(f"  ✅ vLLM 加载成功")
            except Exception as e:
                print(f"❌ 无法加载 vllm embedding: {e}")
                print("  - 使用默认 embedding")
                embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        elif embedding_type == "sentence-transformers":
            model_name_or_path = model_path or "moka-ai/m3e-base"
            print(f"  - 使用 SentenceTransformers")
            print(f"    模型: {model_name_or_path}")
            try:
                from app.core.sentence_embedding_function import SentenceTransformerEmbeddingFunction
                embedding_fn = SentenceTransformerEmbeddingFunction(
                    model_name_or_path=model_name_or_path
                )
                print(f"  ✅ SentenceTransformers 加载成功")
            except Exception as e:
                print(f"❌ 无法加载 SentenceTransformers: {e}")
                print("  - 使用默认 embedding")
                embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        elif embedding_type == "openai":
            print("  - 使用 OpenAI embedding")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❌ 未设置 OPENAI_API_KEY")
                return False
            embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key
            )
        else:
            print("  - 使用默认 embedding (all-MiniLM-L6-v2)")
            embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # 创建新客户端和集合
        new_client = chromadb.PersistentClient(path=self.db_path)
        target_collection = new_collection or self.collection_name

        new_collection_obj = new_client.create_collection(
            name=target_collection,
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

        print(f"  - 新集合已创建: {target_collection}")

        # 4. 重新插入数据
        print(f"\n步骤 4/5: 重新 embedding 并插入数据 (批次大小: {batch_size})")

        success_count = 0
        failed_count = 0

        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_docs + batch_size - 1) // batch_size

            print(f"  - 处理批次 {batch_num}/{total_batches} ({len(batch)} 个文档)...")

            try:
                ids = [doc['id'] for doc in batch]
                texts = [doc['text'] for doc in batch]
                metadatas = [doc['metadata'] for doc in batch]

                new_collection_obj.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )

                success_count += len(batch)
                print(f"    ✅ 成功插入 {len(batch)} 个文档")

            except Exception as e:
                failed_count += len(batch)
                print(f"    ❌ 批次失败: {e}")
                continue

        # 5. 验证
        print("\n步骤 5/5: 验证迁移结果")
        final_count = new_collection_obj.count()

        print(f"\n📊 迁移结果:")
        print(f"  - 原文档数: {total_docs}")
        print(f"  - 成功迁移: {success_count}")
        print(f"  - 失败数量: {failed_count}")
        print(f"  - 最终数量: {final_count}")

        if final_count == total_docs:
            print("\n✅ 迁移成功！")
            # 可以选择删除旧数据库备份
            print(f"\n💡 提示: 旧数据库备份在: {old_db_backup}")
            print("  如确认无误，可以手动删除")
            return True
        else:
            print(f"\n⚠️  迁移不完整 ({final_count}/{total_docs})")
            print(f"  - 可以从备份恢复: {backup_path}")
            return False

    def restore(self, backup_name: str) -> bool:
        """从备份恢复"""
        print(f"\n🔙 正在从备份恢复...")

        backup_path = os.path.join(self.backup_dir, backup_name)

        if not os.path.exists(backup_path):
            print(f"❌ 备份不存在: {backup_path}")
            return False

        try:
            # 删除当前数据库
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)

            # 恢复备份
            shutil.copytree(backup_path, self.db_path)

            print(f"✅ 恢复完成:")
            print(f"  - 从: {backup_path}")
            print(f"  - 到: {self.db_path}")

            return True

        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False

    def list_backups(self):
        """列出所有备份"""
        print("\n📦 可用备份:")

        if not os.path.exists(self.backup_dir):
            print("  (无备份)")
            return

        backups = [d for d in os.listdir(self.backup_dir) if d.startswith("backup_")]

        if not backups:
            print("  (无备份)")
            return

        for backup in sorted(backups, reverse=True):
            backup_path = os.path.join(self.backup_dir, backup)
            size_mb = sum(f.stat().st_size for f in Path(backup_path).rglob('*')) / 1024 / 1024

            # 读取备份信息
            info_file = os.path.join(backup_path, "backup_info.json")
            if os.path.exists(info_file):
                with open(info_file, "r") as f:
                    info = json.load(f)
                    timestamp = info.get('timestamp', 'unknown')
            else:
                timestamp = backup.replace("backup_", "")

            print(f"  - {backup}")
            print(f"    时间: {timestamp}")
            print(f"    大小: {size_mb:.2f} MB")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="向量数据库迁移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查看状态
  python migrate_vectordb.py --status

  # 备份
  python migrate_vectordb.py --backup

  # 导出数据
  python migrate_vectordb.py --export

  # 完整迁移（使用 vLLM）
  python migrate_vectordb.py --migrate --embedding-type vllm

  # 完整迁移（使用 SentenceTransformers，备选方案）
  python migrate_vectordb.py --migrate --embedding-type sentence-transformers

  # 使用本地模型路径
  python migrate_vectordb.py --migrate --embedding-type vllm --model-path /path/to/local/model
  python migrate_vectordb.py --migrate --embedding-type sentence-transformers --model-path /path/to/local/model

  # 列出备份
  python migrate_vectordb.py --list-backups

  # 从备份恢复
  python migrate_vectordb.py --restore backup_20240115_120000
        """
    )

    parser.add_argument("--status", action="store_true", help="显示数据库状态")
    parser.add_argument("--backup", action="store_true", help="备份数据库")
    parser.add_argument("--export", action="store_true", help="导出数据为JSON")
    parser.add_argument("--migrate", action="store_true", help="执行完整迁移")
    parser.add_argument("--restore", metavar="BACKUP", help="从备份恢复")
    parser.add_argument("--list-backups", action="store_true", help="列出所有备份")

    parser.add_argument("--embedding-type", default="vllm",
                        choices=["vllm", "sentence-transformers", "default", "openai"],
                        help="Embedding 模型类型")
    parser.add_argument("--model-path", help="本地模型路径（用于 vllm 和 sentence-transformers）")
    parser.add_argument("--new-collection", help="新集合名称")
    parser.add_argument("--batch-size", type=int, default=100, help="批处理大小")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="数据库路径")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="集合名称")

    args = parser.parse_args()

    # 创建迁移器
    migrator = VectorDBMigrator(
        db_path=args.db_path,
        collection_name=args.collection
    )

    # 执行操作
    if args.status:
        migrator.get_status()
    elif args.backup:
        migrator.backup()
    elif args.export:
        migrator.export_data()
    elif args.migrate:
        migrator.migrate(
            embedding_type=args.embedding_type,
            new_collection=args.new_collection,
            batch_size=args.batch_size,
            model_path=args.model_path
        )
    elif args.restore:
        migrator.restore(args.restore)
    elif args.list_backups:
        migrator.list_backups()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
