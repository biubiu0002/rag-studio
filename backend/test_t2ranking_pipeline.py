"""
T2Ranking数据集导入链路测试脚本

测试完整的导入流程：
1. 加载数据集
2. 创建知识库
3. 导入文档
4. 创建测试集
5. 创建测试用例

用法:
    python test_t2ranking_pipeline.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from app.services.dataset_loader import DatasetService
from app.services.knowledge_base import KnowledgeBaseService
from app.services.document import DocumentService
from app.services.test_service import TestService
from app.schemas.knowledge_base import KnowledgeBaseCreate
from app.schemas.test import TestSetCreate


# 数据集路径配置（请根据实际情况修改）
DATASET_PATHS = {
    "collection": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv",
    "queries": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv",
    "qrels": "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv",
}


async def test_pipeline():
    """测试完整的导入链路"""
    
    print("=" * 60)
    print("T2Ranking数据集导入链路测试")
    print("=" * 60)
    
    # ========== 步骤1: 加载数据集 ==========
    print("\n【步骤1】加载T2Ranking数据集...")
    try:
        dataset = DatasetService.load_t2ranking(
            collection_path=DATASET_PATHS["collection"],
            queries_path=DATASET_PATHS["queries"],
            qrels_path=DATASET_PATHS["qrels"],
            max_docs=100,  # 限制文档数量以加快测试
            max_queries=10  # 限制查询数量
        )
        
        stats = dataset.get_statistics()
        print(f"✅ 数据集加载成功:")
        print(f"   - 文档数: {stats['total_documents']}")
        print(f"   - 查询数: {stats['total_queries']}")
        print(f"   - 有标注的查询数: {stats['queries_with_relevant_docs']}")
        print(f"   - 平均相关文档数: {stats['avg_relevant_docs_per_query']}")
        
    except FileNotFoundError as e:
        print(f"❌ 数据集文件未找到: {e}")
        print(f"请检查路径配置:")
        for key, path in DATASET_PATHS.items():
            print(f"   - {key}: {path}")
        return
    except Exception as e:
        print(f"❌ 加载数据集失败: {e}")
        return
    
    # ========== 步骤2: 创建测试知识库 ==========
    print("\n【步骤2】创建测试知识库...")
    try:
        kb_service = KnowledgeBaseService()
        
        kb_create_data = KnowledgeBaseCreate(
            name="T2Ranking测试知识库",
            description="用于测试T2Ranking数据集导入的知识库",
            embedding_model="bge-m3:latest",
            vector_db_type="chromadb",
        )
        
        kb = await kb_service.create_knowledge_base(kb_create_data)
        print(f"✅ 知识库创建成功:")
        print(f"   - ID: {kb.id}")
        print(f"   - 名称: {kb.name}")
        print(f"   - 向量DB: {kb.vector_db_type}")
        print(f"   - Embedding模型: {kb.embedding_model}")
        
    except Exception as e:
        print(f"❌ 创建知识库失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========== 步骤3: 批量导入文档 ==========
    print("\n【步骤3】批量导入文档到知识库...")
    try:
        document_service = DocumentService()
        
        collection = dataset.load_collection()
        print(f"   准备导入 {len(collection)} 个文档...")
        
        created_docs, failed_docs = await document_service.batch_create_documents_from_dict(
            kb_id=kb.id,
            documents=collection,
            source="t2ranking"
        )
        
        print(f"✅ 文档导入完成:")
        print(f"   - 成功创建: {len(created_docs)} 个")
        print(f"   - 失败: {len(failed_docs)} 个")
        
        if failed_docs:
            print(f"   失败记录（前5条）:")
            for record in failed_docs[:5]:
                print(f"     - {record['external_id']}: {record['error']}")
        
        # 显示部分文档信息
        if created_docs:
            print(f"\n   示例文档:")
            for doc in created_docs[:3]:
                content_preview = doc.content[:50] + "..." if doc.content and len(doc.content) > 50 else doc.content
                print(f"     - {doc.name} (ID: {doc.id}, external_id: {doc.external_id})")
                print(f"       内容预览: {content_preview}")
        
    except Exception as e:
        print(f"❌ 导入文档失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========== 步骤4: 创建测试集 ==========
    print("\n【步骤4】创建测试集...")
    try:
        test_service = TestService()
        
        test_set_create_data = TestSetCreate(
            name="T2Ranking测试集",
            description=f"包含{stats['total_queries']}个查询的检索测试集",
            kb_id=kb.id,
            test_type="retrieval"
        )
        
        test_set = await test_service.create_test_set(test_set_create_data)
        print(f"✅ 测试集创建成功:")
        print(f"   - ID: {test_set.id}")
        print(f"   - 名称: {test_set.name}")
        print(f"   - 类型: {test_set.test_type}")
        
    except Exception as e:
        print(f"❌ 创建测试集失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========== 步骤5: 批量创建测试用例 ==========
    print("\n【步骤5】批量创建测试用例...")
    try:
        # 构建doc_id映射
        external_id_to_doc_id = {doc.external_id: doc.id for doc in created_docs}
        
        # 准备测试用例数据
        test_cases_data = []
        raw_test_cases = dataset.get_test_cases()
        
        for raw_case in raw_test_cases:
            # 映射external_id到新的document_id
            expected_chunks = []
            for external_id in raw_case['relevant_doc_ids']:
                if external_id in external_id_to_doc_id:
                    expected_chunks.append(external_id_to_doc_id[external_id])
            
            if expected_chunks:
                test_cases_data.append({
                    "query": raw_case['query'],
                    "expected_chunks": expected_chunks,
                    "metadata": {
                        "query_id": raw_case['query_id'],
                        "original_doc_ids": raw_case['relevant_doc_ids']
                    }
                })
        
        print(f"   准备创建 {len(test_cases_data)} 个测试用例...")
        
        created_cases, failed_cases = await test_service.batch_create_test_cases(
            test_set_id=test_set.id,
            test_cases_data=test_cases_data
        )
        
        print(f"✅ 测试用例创建完成:")
        print(f"   - 成功创建: {len(created_cases)} 个")
        print(f"   - 失败: {len(failed_cases)} 个")
        
        if failed_cases:
            print(f"   失败记录（前5条）:")
            for record in failed_cases[:5]:
                print(f"     - 索引{record['index']}: {record['error']}")
        
        # 显示部分测试用例
        if created_cases:
            print(f"\n   示例测试用例:")
            for case in created_cases[:3]:
                query_preview = case.query[:50] + "..." if len(case.query) > 50 else case.query
                print(f"     - 查询: {query_preview}")
                print(f"       期望文档数: {len(case.expected_chunks)}")
                print(f"       query_id: {case.metadata.get('query_id')}")
        
    except Exception as e:
        print(f"❌ 创建测试用例失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========== 总结 ==========
    print("\n" + "=" * 60)
    print("✅ 链路测试完成！")
    print("=" * 60)
    print(f"知识库ID: {kb.id}")
    print(f"测试集ID: {test_set.id}")
    print(f"文档数量: {len(created_docs)}")
    print(f"测试用例数量: {len(created_cases)}")
    print("\n下一步:")
    print("1. 文档向量化（待实现）")
    print("2. 执行检索评估（待实现）")
    print("\n可以在前端使用以下ID进行测试:")
    print(f"  - 知识库ID: {kb.id}")
    print(f"  - 测试集ID: {test_set.id}")


if __name__ == "__main__":
    print("开始T2Ranking数据集导入链路测试...\n")
    
    try:
        asyncio.run(test_pipeline())
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n测试执行出错: {e}")
        import traceback
        traceback.print_exc()

