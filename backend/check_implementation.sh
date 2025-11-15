#!/bin/bash

echo "📋 BM25 模型集成检查清单"
echo "=========================================="
echo ""

# 检查修改的文件
echo "✅ 检查修改的文件："
echo ""

files=("requirements.txt" "app/config.py" "app/main.py" "run.py" "app/services/sparse_vector_service.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file 存在"
    else
        echo "  ❌ $file 不存在"
    fi
done

echo ""
echo "✅ 检查新创建的文件："
echo ""

new_files=("scripts/__init__.py" "scripts/download_models.py" "SETUP_BM25_MODEL.md" "BM25_MODEL_IMPLEMENTATION_SUMMARY.md" "test_bm25_setup.py")
for file in "${new_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file 存在"
    else
        echo "  ❌ $file 不存在"
    fi
done

echo ""
echo "✅ 检查核心代码内容："
echo ""

# 检查是否包含关键代码片段
if grep -q "class BM25SparseVectorService" app/services/sparse_vector_service.py; then
    echo "  ✅ BM25SparseVectorService 类已实现"
else
    echo "  ❌ BM25SparseVectorService 类未找到"
fi

if grep -q "dashtext" requirements.txt; then
    echo "  ✅ dashtext 已添加到依赖"
else
    echo "  ❌ dashtext 未添加到依赖"
fi

if grep -q "MODELS_PATH" app/config.py; then
    echo "  ✅ 模型配置已添加"
else
    echo "  ❌ 模型配置未添加"
fi

if grep -q "def ensure_models" run.py; then
    echo "  ✅ 模型下载函数已添加到启动脚本"
else
    echo "  ❌ 模型下载函数未添加到启动脚本"
fi

if grep -q "ensure_models()" run.py; then
    echo "  ✅ 启动时调用了模型下载"
else
    echo "  ❌ 启动时未调用模型下载"
fi

if grep -q "BM25" app/main.py; then
    echo "  ✅ BM25 模型初始化已添加到主程序"
else
    echo "  ❌ BM25 模型初始化未添加到主程序"
fi

if grep -q "download_all_models" scripts/download_models.py; then
    echo "  ✅ 模型下载脚本已实现"
else
    echo "  ❌ 模型下载脚本未实现"
fi

echo ""
echo "=========================================="
echo "✅ 检查完毕！"
echo ""
echo "📚 文档位置："
echo "  - SETUP_BM25_MODEL.md (详细使用指南)"
echo "  - BM25_MODEL_IMPLEMENTATION_SUMMARY.md (实施总结)"
echo ""
echo "🚀 启动应用:"
echo "  python run.py"
echo ""
