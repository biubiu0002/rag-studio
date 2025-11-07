"""
T2Ranking数据集使用示例
演示如何导入和使用T2Ranking数据集进行检索器评估
"""

import asyncio
from app.services.dataset_loader import DatasetService
from app.services.retriever_evaluation import RetrieverEvaluator, RetrievalTestRunner


# 配置T2Ranking数据集路径
COLLECTION_PATH = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv"
QUERIES_PATH = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv"
QRELS_PATH = "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv"


async def example_1_load_dataset():
    """示例1: 加载T2Ranking数据集"""
    print("=" * 60)
    print("示例1: 加载T2Ranking数据集")
    print("=" * 60)
    
    # 加载数据集（建议采样以优化性能）
    dataset = DatasetService.load_t2ranking(
        collection_path=COLLECTION_PATH,
        queries_path=QUERIES_PATH,
        qrels_path=QRELS_PATH,
        max_queries=100,  # 采样100个查询
        max_docs=None     # 自动根据查询确定相关文档
    )
    
    # 获取统计信息
    stats = dataset.get_statistics()
    print("\n数据集统计:")
    print(f"  总文档数: {stats['total_documents']}")
    print(f"  总查询数: {stats['total_queries']}")
    print(f"  平均每个查询的相关文档数: {stats['avg_relevant_docs_per_query']:.2f}")
    
    # 获取测试用例
    test_cases = dataset.get_test_cases(limit=5)
    print(f"\n生成了 {len(test_cases)} 个测试用例")
    print(f"示例查询: {test_cases[0]['query'][:50]}...")
    
    return dataset


async def example_2_evaluate_retriever():
    """示例2: 评估检索器性能"""
    print("\n" + "=" * 60)
    print("示例2: 评估检索器性能")
    print("=" * 60)
    
    # 创建评估器
    evaluator = RetrieverEvaluator(top_k=10)
    
    # 模拟检索结果（实际使用时，这些是从向量数据库检索的结果）
    retrieved_docs = ["doc_1", "doc_2", "doc_5", "doc_10", "doc_15"]
    relevant_docs = ["doc_2", "doc_5", "doc_7", "doc_20"]
    
    # 计算评估指标
    metrics = evaluator.evaluate_single_query(retrieved_docs, relevant_docs)
    
    print("\n评估指标:")
    print(f"  Precision@10: {metrics['precision']:.4f}")
    print(f"  Recall@10: {metrics['recall']:.4f}")
    print(f"  F1-Score: {metrics['f1_score']:.4f}")
    print(f"  MRR: {metrics['mrr']:.4f}")
    print(f"  MAP: {metrics['map']:.4f}")
    print(f"  NDCG: {metrics['ndcg']:.4f}")
    print(f"  Hit Rate: {metrics['hit_rate']:.4f}")


async def example_3_batch_evaluation():
    """示例3: 批量评估多个查询"""
    print("\n" + "=" * 60)
    print("示例3: 批量评估多个查询")
    print("=" * 60)
    
    evaluator = RetrieverEvaluator(top_k=10)
    
    # 模拟多个查询的检索结果
    batch_results = [
        {
            'retrieved_doc_ids': ["doc_1", "doc_2", "doc_3", "doc_4"],
            'relevant_doc_ids': ["doc_2", "doc_3", "doc_5"]
        },
        {
            'retrieved_doc_ids': ["doc_10", "doc_11", "doc_12"],
            'relevant_doc_ids': ["doc_11", "doc_12", "doc_13"]
        },
        {
            'retrieved_doc_ids': ["doc_20", "doc_21"],
            'relevant_doc_ids': ["doc_20", "doc_22", "doc_23"]
        }
    ]
    
    # 批量评估
    avg_metrics = evaluator.evaluate_batch(batch_results)
    
    print(f"\n{len(batch_results)} 个查询的平均性能:")
    print(f"  平均 Precision: {avg_metrics['precision']:.4f}")
    print(f"  平均 Recall: {avg_metrics['recall']:.4f}")
    print(f"  平均 F1-Score: {avg_metrics['f1_score']:.4f}")
    print(f"  平均 MRR: {avg_metrics['mrr']:.4f}")


async def example_4_compare_retrievers():
    """示例4: 对比不同检索器配置"""
    print("\n" + "=" * 60)
    print("示例4: 对比不同检索器配置")
    print("=" * 60)
    
    evaluator = RetrieverEvaluator(top_k=10)
    
    # 相同查询的相关文档
    relevant_docs = ["doc_2", "doc_5", "doc_7", "doc_10"]
    
    # 配置A的检索结果（如 BM25）
    config_a_results = ["doc_1", "doc_2", "doc_5", "doc_8", "doc_9"]
    metrics_a = evaluator.evaluate_single_query(config_a_results, relevant_docs)
    
    # 配置B的检索结果（如 Dense Retrieval）
    config_b_results = ["doc_2", "doc_5", "doc_7", "doc_10", "doc_12"]
    metrics_b = evaluator.evaluate_single_query(config_b_results, relevant_docs)
    
    print("\n配置对比:")
    print(f"配置A (BM25):")
    print(f"  F1-Score: {metrics_a['f1_score']:.4f}")
    print(f"  NDCG: {metrics_a['ndcg']:.4f}")
    
    print(f"\n配置B (Dense Retrieval):")
    print(f"  F1-Score: {metrics_b['f1_score']:.4f}")
    print(f"  NDCG: {metrics_b['ndcg']:.4f}")
    
    # 判断哪个配置更好
    winner = "配置B" if metrics_b['f1_score'] > metrics_a['f1_score'] else "配置A"
    print(f"\n结论: {winner} 性能更优")


async def main():
    """运行所有示例"""
    print("\n" + "📚" * 30)
    print("T2Ranking数据集使用示例")
    print("📚" * 30 + "\n")
    
    # 示例1: 加载数据集
    await example_1_load_dataset()
    
    # 示例2: 评估检索器
    await example_2_evaluate_retriever()
    
    # 示例3: 批量评估
    await example_3_batch_evaluation()
    
    # 示例4: 对比配置
    await example_4_compare_retrievers()
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("  - 使用 max_queries 参数控制数据集规模")
    print("  - 建议从100个查询开始测试")
    print("  - 评估指标越接近1.0越好")
    print("  - F1-Score平衡了精确率和召回率")
    print("  - NDCG考虑了检索结果的排序质量")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

