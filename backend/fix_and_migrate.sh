#!/bin/bash
# 向量数据库迁移修复脚本
# 在服务器上运行此脚本以修复并完成迁移

echo "🔧 向量数据库迁移修复工具"
echo "================================"
echo ""

# 检查当前目录
if [ ! -f "migrate_vectordb.py" ]; then
    echo "❌ 错误: 请在 backend 目录下运行此脚本"
    exit 1
fi

echo "步骤 1/3: 恢复到初始状态"
echo "----------------------------"

# 恢复旧数据库
if [ -d "chroma_db_old" ]; then
    echo "发现 chroma_db_old，正在恢复..."
    rm -rf chroma_db
    mv chroma_db_old chroma_db
    echo "✅ 已恢复原始数据库"
else
    echo "⚠️  未发现 chroma_db_old，跳过恢复"
fi

echo ""
echo "步骤 2/3: 检查当前状态"
echo "----------------------------"
python migrate_vectordb.py --status

echo ""
echo "步骤 3/3: 执行迁移"
echo "----------------------------"
echo "请选择 embedding 类型:"
echo "  1) vllm (推荐，中文效果好，需要 GPU)"
echo "  2) default (备选，无需 GPU)"
echo "  3) openai (需要 API Key)"
echo ""
read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "使用 vllm embedding..."
        python migrate_vectordb.py --migrate --embedding-type vllm --batch-size 50
        ;;
    2)
        echo ""
        echo "使用 default embedding..."
        python migrate_vectordb.py --migrate --embedding-type default --batch-size 50
        ;;
    3)
        echo ""
        read -p "请输入 OPENAI_API_KEY: " api_key
        export OPENAI_API_KEY="$api_key"
        echo "使用 OpenAI embedding..."
        python migrate_vectordb.py --migrate --embedding-type openai --batch-size 50
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "✅ 迁移完成！"
echo ""
echo "💡 下一步："
echo "  1. 检查迁移结果: python migrate_vectordb.py --status"
echo "  2. 测试搜索功能: 启动后端并测试 API"
echo "  3. 确认无误后删除备份: rm -rf chroma_db_old"
echo ""
