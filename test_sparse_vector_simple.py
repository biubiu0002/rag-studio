#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版测试稀疏向量生成功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, backend_path)

# 设置环境变量
os.environ['PYTHONPATH'] = backend_path

def test_bm25_sparse_vector():
    """测试BM25稀疏向量生成"""
    print("测试BM25稀疏向量生成...")
    
    # 动态导入
    from app.services.sparse_vector_service import SparseVectorServiceFactory
    
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


def test_other_sparse_vectors():
    """测试其他稀疏向量生成方法"""
    print("\n测试其他稀疏向量生成方法...")
    
    # 动态导入
    from app.services.sparse_vector_service import SparseVectorServiceFactory
    
    # 测试TF-IDF
    tfidf_service = SparseVectorServiceFactory.create("tf-idf")
    
    # 添加测试文档
    test_docs = [
        "人工智能 机器学习 深度学习",
        "自然语言处理 计算机视觉",
        "数据科学 大数据"
    ]
    
    for doc in test_docs:
        tfidf_service.add_document(doc)
    
    # 生成查询的稀疏向量
    query = "人工智能 学习"
    tfidf_vector = tfidf_service.generate_sparse_vector(query)
    
    print(f"TF-IDF稀疏向量: {tfidf_vector}")
    
    # 测试简单稀疏向量
    simple_service = SparseVectorServiceFactory.create("simple")
    simple_vector = simple_service.generate_sparse_vector(query)
    
    print(f"简单稀疏向量: {simple_vector}")
    
    print("其他稀疏向量生成测试通过！")


def main():
    """主函数"""
    print("开始测试稀疏向量生成功能...")
    
    try:
        test_bm25_sparse_vector()
        test_other_sparse_vectors()
        
        print("\n所有测试通过！")
        return 0
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)