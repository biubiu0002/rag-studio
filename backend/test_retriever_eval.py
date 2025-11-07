"""
检索器评估系统测试脚本
用于验证T2Ranking数据集加载和评估功能
"""

import asyncio
from app.services.dataset_loader import DatasetService
from app.services.retriever_evaluation import RetrieverEvaluator


async def test_t2ranking_loader():
    """测试T2Ranking数据集加载"""
    print("=" * 60)
    print("测试 T2Ranking 数据集加载")
    print("=" * 60)
    
    # 数据集路径
    collection_path = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv"
    queries_path = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv"
    qrels_path = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv"
    
    try:
        # 加载数据集（采样）
        dataset = DatasetService.load_t2ranking(
            collection_path=collection_path,
            queries_path=queries_path,
            qrels_path=qrels_path,
            max_queries=10,  # 只加载10个查询用于测试
            max_docs=1000    # 最多1000个文档
        )
        
        # 获取统计信息
        stats = dataset.get_statistics()
        print("\n数据集统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 获取测试用例
        test_cases = dataset.get_test_cases(limit=5)
        print(f"\n生成 {len(test_cases)} 个测试用例（示例）:")
        for i, case in enumerate(test_cases[:3], 1):
            print(f"\n测试用例 {i}:")
            print(f"  Query ID: {case['query_id']}")
            print(f"  Query: {case['query'][:100]}...")
            print(f"  相关文档数: {len(case['relevant_doc_ids'])}")
            print(f"  相关文档ID: {case['relevant_doc_ids'][:5]}...")
        
        print("\n✅ T2Ranking数据集加载测试通过！")
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        print("请确保数据集文件路径正确")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_retriever_evaluator():
    """测试检索器评估功能"""
    print("\n" + "=" * 60)
    print("测试检索器评估功能")
    print("=" * 60)
    
    try:
        # 创建评估器
        evaluator = RetrieverEvaluator(top_k=10)
        
        # 模拟检索结果
        retrieved_doc_ids = ["doc_1", "doc_2", "doc_5", "doc_10", "doc_15"]
        relevant_doc_ids = ["doc_2", "doc_5", "doc_7", "doc_20"]
        
        print("\n模拟检索场景:")
        print(f"  检索到的文档: {retrieved_doc_ids}")
        print(f"  相关的文档: {relevant_doc_ids}")
        
        # 评估单个查询
        metrics = evaluator.evaluate_single_query(
            retrieved_doc_ids=retrieved_doc_ids,
            relevant_doc_ids=relevant_doc_ids
        )
        
        print("\n评估指标:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value:.4f}")
        
        # 批量评估
        batch_results = [
            {
                'retrieved_doc_ids': ["doc_1", "doc_2", "doc_3"],
                'relevant_doc_ids': ["doc_2", "doc_3", "doc_4"]
            },
            {
                'retrieved_doc_ids': ["doc_5", "doc_6", "doc_7"],
                'relevant_doc_ids': ["doc_7", "doc_8"]
            },
            {
                'retrieved_doc_ids': ["doc_10", "doc_11"],
                'relevant_doc_ids': ["doc_10", "doc_11", "doc_12"]
            }
        ]
        
        avg_metrics = evaluator.evaluate_batch(batch_results)
        
        print("\n批量评估平均指标:")
        for metric_name, value in avg_metrics.items():
            print(f"  {metric_name}: {value:.4f}")
        
        print("\n✅ 检索器评估功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("检索器评估系统测试")
    print("🚀" * 30 + "\n")
    
    # 测试数据集加载
    result1 = await test_t2ranking_loader()
    
    # 测试评估功能
    result2 = await test_retriever_evaluator()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"T2Ranking数据集加载: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"检索器评估功能: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result1 and result2:
        print("\n🎉 所有测试通过！检索器评估系统已就绪。")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息。")


if __name__ == "__main__":
    asyncio.run(main())

