"""
API测试脚本
用于快速测试后端API功能
"""

import asyncio
import httpx

API_BASE = "http://localhost:8000/api/v1"


async def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")


async def test_create_knowledge_base():
    """测试创建知识库"""
    print("\n=== 测试创建知识库 ===")
    data = {
        "name": "测试知识库",
        "description": "这是一个测试知识库",
        "embedding_model": "nomic-embed-text",
        "embedding_dimension": 768,
        "vector_db_type": "qdrant",
        "chunk_size": 512,
        "chunk_overlap": 50,
        "retrieval_top_k": 5,
        "retrieval_score_threshold": 0.7
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE}/knowledge-bases", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        
        if result.get("success"):
            return result["data"]["id"]
    
    return None


async def test_list_knowledge_bases():
    """测试获取知识库列表"""
    print("\n=== 测试获取知识库列表 ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/knowledge-bases")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")
        print(f"知识库数量: {result.get('total', 0)}")


async def test_get_knowledge_base(kb_id: str):
    """测试获取知识库详情"""
    print(f"\n=== 测试获取知识库详情: {kb_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/knowledge-bases/{kb_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_update_knowledge_base(kb_id: str):
    """测试更新知识库"""
    print(f"\n=== 测试更新知识库: {kb_id} ===")
    data = {
        "name": "更新后的知识库名称",
        "description": "更新后的描述",
        "chunk_size": 256
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{API_BASE}/knowledge-bases/{kb_id}", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_get_knowledge_base_config(kb_id: str):
    """测试获取知识库配置"""
    print(f"\n=== 测试获取知识库配置: {kb_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/knowledge-bases/{kb_id}/config")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def test_delete_knowledge_base(kb_id: str):
    """测试删除知识库"""
    print(f"\n=== 测试删除知识库: {kb_id} ===")
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_BASE}/knowledge-bases/{kb_id}")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")


async def main():
    """主测试流程"""
    print("开始测试API...")
    
    try:
        # 1. 健康检查
        await test_health()
        
        # 2. 创建知识库
        kb_id = await test_create_knowledge_base()
        
        if kb_id:
            # 3. 获取知识库列表
            await test_list_knowledge_bases()
            
            # 4. 获取知识库详情
            await test_get_knowledge_base(kb_id)
            
            # 5. 更新知识库
            await test_update_knowledge_base(kb_id)
            
            # 6. 获取知识库配置
            await test_get_knowledge_base_config(kb_id)
            
            # 7. 再次获取详情确认更新
            await test_get_knowledge_base(kb_id)
            
            # 8. 删除知识库
            await test_delete_knowledge_base(kb_id)
            
            # 9. 确认删除
            await test_list_knowledge_bases()
        
        print("\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

