#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试稀疏向量生成功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 添加backend目录到Python路径
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, backend_path)

# 设置PYTHONPATH环境变量
os.environ['PYTHONPATH'] = backend_path

from app.services.retrieval_service import RetrievalService
from app.services.sparse_vector_service import SparseVectorServiceFactory


async def test_bm25_sparse_vector():
    """测试BM25稀疏向量生成"""
    print("测试BM25稀疏向量生成...")
    
    # 创建稀疏向量服务
    bm25_service = SparseVectorServiceFactory.create("bm25")
    
    # 添加一些测试文档
    test_docs = [
        "这是一个测试文档，包含一些关键词。",
        "另一个测试文档，也包含关键词和一些其他内容。",
        "第三个文档，用于测试BM25算法的实现。"
    ]
    
    # 添加文档到语料库
    for doc in test_docs:
        bm25_service.add_document(doc)
    
    # 生成查询的稀疏向量
    query = "测试 关键词"
    sparse_vector = bm25_service.generate_sparse_vector(query)
    
    print(f"查询: {query}")
    print(f"稀疏向量: {sparse_vector}")
    
    # 验证结果
    assert isinstance(sparse_vector, dict), "稀疏向量应该是字典类型"
    assert len(sparse_vector) > 0, "稀疏向量不应该为空"
    
    print("BM25稀疏向量生成测试通过！")


async def test_retrieval_service_sparse_vector():
    """测试检索服务中的稀疏向量生成功能"""
    print("\n测试检索服务中的稀疏向量生成功能...")
    
    # 创建检索服务
    retrieval_service = RetrievalService()
    
    # 测试文本
    text = "人工智能 机器学习 深度学习"
    
    # 生成BM25稀疏向量（不依赖知识库）
    sparse_vector = await retrieval_service.generate_sparse_vector("test_kb", text, method="bm25")
    
    print(f"文本: {text}")
    print(f"BM25稀疏向量: {sparse_vector}")
    
    # 生成TF-IDF稀疏向量
    tfidf_vector = await retrieval_service.generate_sparse_vector("test_kb", text, method="tf-idf")
    
    print(f"TF-IDF稀疏向量: {tfidf_vector}")
    
    # 生成简单稀疏向量
    simple_vector = await retrieval_service.generate_sparse_vector("test_kb", text, method="simple")
    
    print(f"简单稀疏向量: {simple_vector}")
    
    print("检索服务稀疏向量生成测试完成！")


async def main():
    """主函数"""
    print("开始测试稀疏向量生成功能...")
    
    try:
        await test_bm25_sparse_vector()
        await test_retrieval_service_sparse_vector()
        
        print("\n所有测试通过！")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)