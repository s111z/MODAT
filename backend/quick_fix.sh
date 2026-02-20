#!/bin/bash
# 快速修复脚本 - 服务器端执行

echo "🔧 向量数据库迁移 - 快速修复"
echo "===================================="
echo ""

# 检查当前目录
if [ ! -f "migrate_vectordb.py" ]; then
    echo "❌ 错误: 请在 backend 目录下运行此脚本"
    exit 1
fi

echo "步骤 1: 恢复数据库到初始状态"
echo "----------------------------"
if [ -d "chroma_db_old" ]; then
    echo "发现 chroma_db_old，正在恢复..."
    rm -rf chroma_db
    mv chroma_db_old chroma_db
    echo "✅ 已恢复"
else
    echo "⚠️  未发现 chroma_db_old，数据库状态正常"
fi

echo ""
echo "步骤 2: 选择 Embedding 方案"
echo "----------------------------"
echo ""
echo "请选择 embedding 模型:"
echo ""
echo "  1) vLLM + Qwen3-Embedding-0.6B"
echo "     - 🌟 最佳中文效果 (512维)"
echo "     - 需要: CUDA GPU, ~2GB 显存"
echo "     - 依赖: pip install vllm"
echo ""
echo "  2) SentenceTransformers + m3e-base"
echo "     - 🎯 平衡选择 (768维)"
echo "     - 需要: CPU 或 GPU 均可, ~400MB 内存"
echo "     - 依赖: pip install sentence-transformers"
echo ""
echo "  3) 默认模型 (all-MiniLM-L6-v2)"
echo "     - ⚡ 快速部署 (384维)"
echo "     - 需要: 无额外依赖"
echo "     - ⚠️  中文效果较差"
echo ""
read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "检查 vLLM 安装状态..."
        if python -c "import vllm" 2>/dev/null; then
            echo "✅ vLLM 已安装"
        else
            echo "❌ vLLM 未安装"
            read -p "是否现在安装 vLLM? (y/n): " install_vllm
            if [ "$install_vllm" = "y" ]; then
                echo "正在安装 vLLM..."
                pip install vllm
                if [ $? -eq 0 ]; then
                    echo "✅ vLLM 安装成功"
                else
                    echo "❌ vLLM 安装失败，请手动安装后重试"
                    exit 1
                fi
            else
                echo "❌ 取消迁移"
                exit 1
            fi
        fi

        echo ""
        echo "开始迁移（使用 vLLM）..."
        python migrate_vectordb.py --migrate --embedding-type vllm --batch-size 50
        ;;

    2)
        echo ""
        echo "检查 SentenceTransformers 安装状态..."
        if python -c "import sentence_transformers" 2>/dev/null; then
            echo "✅ SentenceTransformers 已安装"
        else
            echo "❌ SentenceTransformers 未安装"
            read -p "是否现在安装 SentenceTransformers? (y/n): " install_st
            if [ "$install_st" = "y" ]; then
                echo "正在安装 SentenceTransformers..."
                pip install sentence-transformers
                if [ $? -eq 0 ]; then
                    echo "✅ SentenceTransformers 安装成功"
                else
                    echo "❌ SentenceTransformers 安装失败，请手动安装后重试"
                    exit 1
                fi
            else
                echo "❌ 取消迁移"
                exit 1
            fi
        fi

        echo ""
        echo "开始迁移（使用 SentenceTransformers）..."
        python migrate_vectordb.py --migrate --embedding-type sentence-transformers --batch-size 50
        ;;

    3)
        echo ""
        echo "开始迁移（使用默认模型）..."
        echo "⚠️  警告: 默认模型对中文支持较差"
        python migrate_vectordb.py --migrate --embedding-type default --batch-size 50
        ;;

    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "===================================="
echo "✅ 迁移完成！"
echo ""
echo "📋 验证迁移结果:"
echo "  python migrate_vectordb.py --status"
echo ""
echo "🧪 测试搜索功能:"
echo "  python -c \"from app.core.vector_store import VectorDBManager; db = VectorDBManager(); print(db.search('测试', top_k=3))\""
echo ""
echo "🗑️  清理旧数据（确认无误后）:"
echo "  rm -rf chroma_db_old"
echo ""
