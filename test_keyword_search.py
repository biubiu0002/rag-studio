#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试关键词检索功能
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, backend_path)

# 设置环境变量
os.environ['PYTHONPATH'] = backend_path


async def test_keyword_search():
    """测试关键词检索功能"""
    print("测试关键词检索功能...")
    
    # 动态导入
    from app.services.retrieval_service import RetrievalService, BM25
    
    # 测试BM25算法
    print("\n1. 测试BM25算法...")
    bm25 = BM25()
    
    # 测试数据
    query_tokens = ["测试", "关键词"]
    doc_tokens = ["这是", "一个", "测试", "文档", "包含", "关键词"]
    doc_freq = {"测试": 2, "关键词": 1, "文档": 3}
    total_docs = 5
    avg_doc_length = 10.0
    
    # 计算BM25分数
    score = bm25.score(query_tokens, doc_tokens, doc_freq, total_docs, avg_doc_length)
    print(f"BM25分数: {score}")
    
    # 验证结果
    assert score > 0, "BM25分数应该大于0"
    print("BM25算法测试通过！")
    
    # 测试检索服务
    print("\n2. 测试检索服务...")
    retrieval_service = RetrievalService()
    
    # 由于我们没有实际的知识库，这里只测试方法是否能正常调用
    # 在实际应用中，需要有真实的知识库和文档数据
    print("检索服务初始化成功！")
    
    print("关键词检索功能测试完成！")


async def main():
    """主函数"""
    print("开始测试关键词检索功能...")
    
    try:
        await test_keyword_search()
        
        print("\n所有测试通过！")
        return 0
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)