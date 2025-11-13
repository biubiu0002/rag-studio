"""
新测试管理API测试脚本
用于测试检索器和生成测试用例的API功能
"""

import asyncio
import httpx

API_BASE = "http://localhost:8000/api/v1"


async def test_create_test_set():
    """测试创建测试集"""
    print("\n=== 测试创建测试集 ===")
    data = {
        "name": "检索器测试集_示例",
        "description": "用于测试新API的示例测试集",
        "kb_id": "kb_test_001",
        "test_type": "retrieval"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/tests/test-sets", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get("success"):
            return result["data"]["id"]
    
    return None


async def test_create_retriever_test_case(test_set_id: str):
    """测试创建检索器测试用例"""
    print(f"\n=== 测试创建检索器测试用例: test_set_id={test_set_id} ===")
    data = {
        "test_set_id": test_set_id,
        "question": "Python中如何定义一个类？",
        "expected_answers": [
            {
                "answer_text": "Python使用class关键字定义类",
                "chunk_id": "chunk_010",
                "relevance_score": 1.0
            },
            {
                "answer_text": "类定义语法：class ClassName:",
                "chunk_id": "chunk_011",
                "relevance_score": 0.9
            }
        ],
        "metadata": {"difficulty": "easy"}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/tests/retriever/cases", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get("success"):
            return result["data"]["id"]
    
    return None


async def test_batch_create_retriever_test_cases(test_set_id: str):
    """测试批量创建检索器测试用例"""
    print(f"\n=== 测试批量创建检索器测试用例: test_set_id={test_set_id} ===")
    data = {
        "test_set_id": test_set_id,
        "cases": [
            {
                "question": "什么是面向对象编程？",
                "expected_answers": [
                    {
                        "answer_text": "面向对象编程是一种编程范式",
                        "chunk_id": "chunk_020",
                        "relevance_score": 1.0
                    }
                ],
                "metadata": {"difficulty": "medium"}
            },
            {
                "question": "Python的继承机制如何工作？",
                "expected_answers": [
                    {
                        "answer_text": "Python支持单继承和多继承",
                        "chunk_id": "chunk_030",
                        "relevance_score": 1.0
                    }
                ],
                "metadata": {"difficulty": "hard"}
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/tests/retriever/cases/batch", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_list_retriever_test_cases(test_set_id: str):
    """测试获取检索器测试用例列表"""
    print(f"\n=== 测试获取检索器测试用例列表: test_set_id={test_set_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/tests/retriever/cases",
            params={"test_set_id": test_set_id, "page": 1, "page_size": 10}
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        print(f"测试用例数量: {result.get('total', 0)}")


async def test_get_retriever_test_case(case_id: str):
    """测试获取检索器测试用例详情"""
    print(f"\n=== 测试获取检索器测试用例详情: case_id={case_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/tests/retriever/cases/{case_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_update_retriever_test_case(case_id: str):
    """测试更新检索器测试用例"""
    print(f"\n=== 测试更新检索器测试用例: case_id={case_id} ===")
    data = {
        "question": "Python中如何定义一个类？（已更新）",
        "metadata": {"difficulty": "easy", "updated": True}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{API_BASE}/tests/retriever/cases/{case_id}", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_add_expected_answer(case_id: str):
    """测试添加期望答案"""
    print(f"\n=== 测试添加期望答案: case_id={case_id} ===")
    data = {
        "answer_text": "新增的答案：类是对象的模板",
        "chunk_id": "chunk_012",
        "relevance_score": 0.85
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/tests/retriever/cases/{case_id}/answers", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_create_generation_test_case(test_set_id: str):
    """测试创建生成测试用例"""
    print(f"\n=== 测试创建生成测试用例: test_set_id={test_set_id} ===")
    data = {
        "test_set_id": test_set_id,
        "question": "什么是面向对象编程？",
        "reference_answer": "面向对象编程是一种编程范式，它使用对象和类的概念来组织代码。",
        "reference_contexts": [
            "面向对象编程的核心概念包括封装、继承和多态",
            "OOP是一种将数据和操作数据的方法组合在一起的编程方式"
        ],
        "metadata": {"difficulty": "medium"}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/tests/generation/cases", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get("success"):
            return result["data"]["id"]
    
    return None


async def test_list_generation_test_cases(test_set_id: str):
    """测试获取生成测试用例列表"""
    print(f"\n=== 测试获取生成测试用例列表: test_set_id={test_set_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/tests/generation/cases",
            params={"test_set_id": test_set_id, "page": 1, "page_size": 10}
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        print(f"测试用例数量: {result.get('total', 0)}")


async def test_delete_retriever_test_case(case_id: str):
    """测试删除检索器测试用例"""
    print(f"\n=== 测试删除检索器测试用例: case_id={case_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_BASE}/tests/retriever/cases/{case_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def main():
    """主测试流程"""
    print("开始测试新的测试管理API...")
    
    try:
        # 1. 创建测试集
        test_set_id = await test_create_test_set()
        
        if not test_set_id:
            print("❌ 创建测试集失败，无法继续测试")
            return
        
        # 2. 创建检索器测试用例
        case_id = await test_create_retriever_test_case(test_set_id)
        
        # 3. 批量创建检索器测试用例
        await test_batch_create_retriever_test_cases(test_set_id)
        
        # 4. 获取检索器测试用例列表
        await test_list_retriever_test_cases(test_set_id)
        
        if case_id:
            # 5. 获取检索器测试用例详情
            await test_get_retriever_test_case(case_id)
            
            # 6. 更新检索器测试用例
            await test_update_retriever_test_case(case_id)
            
            # 7. 添加期望答案
            await test_add_expected_answer(case_id)
            
            # 8. 再次获取详情确认更新
            await test_get_retriever_test_case(case_id)
        
        # 9. 创建生成测试用例
        gen_case_id = await test_create_generation_test_case(test_set_id)
        
        # 10. 获取生成测试用例列表
        await test_list_generation_test_cases(test_set_id)
        
        print("\n✅ 所有测试完成!")
        print(f"测试集ID: {test_set_id}")
        print(f"检索器测试用例ID: {case_id}")
        print(f"生成测试用例ID: {gen_case_id}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
