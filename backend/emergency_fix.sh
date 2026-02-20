#!/bin/bash
# 应急修复脚本 - 修复 Collection 已存在错误

echo "🔧 应急修复 - Collection 已存在错误"
echo "===================================="
echo ""

cd /root/app/MOTA/backend

echo "步骤 1: 检查当前状态"
echo "----------------------------"
ls -la | grep chroma

echo ""
echo "步骤 2: 清理所有数据库目录"
echo "----------------------------"
read -p "是否要删除所有 chroma_db 相关目录? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "❌ 取消操作"
    exit 1
fi

echo "正在删除..."
rm -rf chroma_db chroma_db_old
echo "✅ 清理完成"

echo ""
echo "步骤 3: 检查备份"
echo "----------------------------"
ls -la chroma_db_backups/ | tail -5

echo ""
echo "步骤 4: 从最新备份恢复"
echo "----------------------------"
latest_backup=$(ls -t chroma_db_backups/ | head -1)
echo "最新备份: $latest_backup"

if [ -z "$latest_backup" ]; then
    echo "❌ 没有找到备份"
    exit 1
fi

read -p "是否从 $latest_backup 恢复? (y/n): " restore

if [ "$restore" = "y" ]; then
    cp -r "chroma_db_backups/$latest_backup" chroma_db
    echo "✅ 恢复完成"
fi

echo ""
echo "步骤 5: 验证状态"
echo "----------------------------"
python migrate_vectordb.py --status

echo ""
echo "===================================="
echo "修复完成！现在可以重新执行迁移:"
echo ""
echo "  python migrate_vectordb.py --migrate --embedding-type sentence-transformers"
echo ""
