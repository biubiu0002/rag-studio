"""
测试管理控制器
"""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.schemas.test import (
    TestSetCreate,
    TestSetUpdate,
    TestSetResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    RunRetrievalTestRequest,
    RetrievalTestResultResponse,
    RunGenerationTestRequest,
    GenerationTestResultResponse,
)
from app.core.response import success_response, page_response, error_response
from app.core.exceptions import NotFoundException, BadRequestException
from app.services.test_service import TestService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tests", tags=["测试管理"])


# ========== 测试集管理 ==========

@router.post("/test-sets", response_model=None, summary="创建测试集")
async def create_test_set(data: TestSetCreate):
    """
    创建测试集
    
    - **name**: 测试集名称
    - **kb_id**: 关联的知识库ID
    - **test_type**: 测试类型（retrieval/generation）
    - **配置快照**: 可选，如果不提供则从知识库自动获取
    """
    try:
        # 验证知识库是否存在
        from app.services.knowledge_base import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        kb = await kb_service.get_knowledge_base(data.kb_id)
        if not kb:
            return JSONResponse(
                status_code=404,
                content=error_response(
                    message=f"知识库不存在: {data.kb_id}"
                )
            )
        
        # 创建测试集
        test_service = TestService()
        test_set = await test_service.create_test_set(data)
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        test_set_dict = test_set.model_dump()
        response_data = TestSetResponse.model_validate(test_set_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="测试集创建成功"
            )
        )
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"创建测试集失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"创建测试集失败: {str(e)}")
        )


@router.get("/test-sets", response_model=None, summary="获取测试集列表")
async def list_test_sets(
    kb_id: str = Query(None, description="知识库ID筛选"),
    test_type: str = Query(None, description="测试类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取测试集列表
    """
    try:
        from app.models.test import TestType
        
        test_service = TestService()
        test_type_enum = None
        if test_type:
            try:
                test_type_enum = TestType(test_type)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content=error_response(message=f"无效的测试类型: {test_type}")
                )
        
        test_sets, total = await test_service.list_test_sets(
            kb_id=kb_id,
            test_type=test_type_enum,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        response_data = []
        for ts in test_sets:
            ts_dict = ts.model_dump()
            response_data.append(TestSetResponse.model_validate(ts_dict).model_dump())
        
        return JSONResponse(
            content=page_response(
                data=response_data,
                total=total,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        logger.error(f"获取测试集列表失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取测试集列表失败: {str(e)}")
        )


@router.get("/test-sets/{test_set_id}", response_model=None, summary="获取测试集详情")
async def get_test_set(test_set_id: str):
    """
    根据ID获取测试集详情
    """
    try:
        test_service = TestService()
        test_set = await test_service.get_test_set(test_set_id)
        
        if not test_set:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试集不存在: {test_set_id}")
            )
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        test_set_dict = test_set.model_dump()
        response_data = TestSetResponse.model_validate(test_set_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="获取测试集详情成功"
            )
        )
    except Exception as e:
        logger.error(f"获取测试集详情失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取测试集详情失败: {str(e)}")
        )


@router.put("/test-sets/{test_set_id}", response_model=None, summary="更新测试集")
async def update_test_set(test_set_id: str, data: TestSetUpdate):
    """
    更新测试集
    """
    try:
        test_service = TestService()
        test_set = await test_service.update_test_set(test_set_id, data)
        
        if not test_set:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试集不存在: {test_set_id}")
            )
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        test_set_dict = test_set.model_dump()
        response_data = TestSetResponse.model_validate(test_set_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="测试集更新成功"
            )
        )
    except Exception as e:
        logger.error(f"更新测试集失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"更新测试集失败: {str(e)}")
        )


@router.delete("/test-sets/{test_set_id}", response_model=None, summary="删除测试集")
async def delete_test_set(test_set_id: str):
    """
    删除测试集
    
    注意：会同时删除测试集下的所有测试用例
    """
    try:
        test_service = TestService()
        
        # 检查测试集是否存在
        test_set = await test_service.get_test_set(test_set_id)
        if not test_set:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试集不存在: {test_set_id}")
            )
        
        # 删除测试集（级联删除测试用例）
        deleted = await test_service.delete_test_set(test_set_id)
        
        if not deleted:
            return JSONResponse(
                status_code=500,
                content=error_response(message="删除测试集失败")
            )
        
        return JSONResponse(
            content=success_response(
                message="测试集删除成功"
            )
        )
    except Exception as e:
        logger.error(f"删除测试集失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"删除测试集失败: {str(e)}")
        )


# ========== 测试用例管理 ==========

@router.post("/test-cases", response_model=None, summary="创建测试用例")
async def create_test_case(data: TestCaseCreate):
    """
    创建测试用例
    
    - **test_set_id**: 所属测试集ID
    - **query**: 测试问题
    - **expected_chunks**: 期望检索到的分块ID列表
    - **expected_answer**: 期望的答案
    - **metadata**: 测试用例元数据（可选）
    """
    try:
        test_service = TestService()
        test_case = await test_service.create_test_case(data)
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        test_case_dict = test_case.model_dump()
        response_data = TestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="测试用例创建成功"
            )
        )
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"创建测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"创建测试用例失败: {str(e)}")
        )


@router.get("/test-cases", response_model=None, summary="获取测试用例列表")
async def list_test_cases(
    test_set_id: str = Query(..., description="测试集ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取测试集的测试用例列表
    """
    try:
        test_service = TestService()
        test_cases, total = await test_service.list_test_cases(
            test_set_id=test_set_id,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        response_data = []
        for tc in test_cases:
            tc_dict = tc.model_dump()
            response_data.append(TestCaseResponse.model_validate(tc_dict).model_dump())
        
        return JSONResponse(
            content=page_response(
                data=response_data,
                total=total,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        logger.error(f"获取测试用例列表失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取测试用例列表失败: {str(e)}")
        )


@router.get("/test-cases/{test_case_id}", response_model=None, summary="获取测试用例详情")
async def get_test_case(test_case_id: str):
    """
    根据ID获取测试用例详情
    """
    try:
        test_service = TestService()
        test_case = await test_service.get_test_case(test_case_id)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {test_case_id}")
            )
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        test_case_dict = test_case.model_dump()
        response_data = TestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="获取测试用例详情成功"
            )
        )
    except Exception as e:
        logger.error(f"获取测试用例详情失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取测试用例详情失败: {str(e)}")
        )


@router.put("/test-cases/{test_case_id}", response_model=None, summary="更新测试用例")
async def update_test_case(test_case_id: str, data: TestCaseUpdate):
    """
    更新测试用例
    """
    try:
        test_service = TestService()
        test_case = await test_service.update_test_case(test_case_id, data)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {test_case_id}")
            )
        
        # 转换为响应格式（先序列化为字典，datetime会自动转换为ISO字符串）
        test_case_dict = test_case.model_dump()
        response_data = TestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="测试用例更新成功"
            )
        )
    except Exception as e:
        logger.error(f"更新测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"更新测试用例失败: {str(e)}")
        )


@router.delete("/test-cases/{test_case_id}", response_model=None, summary="删除测试用例")
async def delete_test_case(test_case_id: str):
    """
    删除测试用例
    """
    try:
        test_service = TestService()
        
        # 检查测试用例是否存在
        test_case = await test_service.get_test_case(test_case_id)
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {test_case_id}")
            )
        
        # 删除测试用例
        deleted = await test_service.delete_test_case(test_case_id)
        
        if not deleted:
            return JSONResponse(
                status_code=500,
                content=error_response(message="删除测试用例失败")
            )
        
        return JSONResponse(
            content=success_response(
                message="测试用例删除成功"
            )
        )
    except Exception as e:
        logger.error(f"删除测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"删除测试用例失败: {str(e)}")
        )


# ========== 检索测试 ==========

@router.post("/retrieval/run", response_model=None, summary="执行检索测试")
async def run_retrieval_test(data: RunRetrievalTestRequest):
    """
    执行检索测试
    
    - **test_case_id**: 单个测试用例ID（单次测试）
    - **test_set_id**: 测试集ID（批量测试）
    
    二选一，优先使用 test_case_id
    """
    # TODO: 实现执行检索测试逻辑
    return JSONResponse(
        content=success_response(
            data={"task_id": "task_temp_001"},
            message="检索测试已启动（待实现）"
        )
    )


@router.get("/retrieval/results", response_model=None, summary="获取检索测试结果")
async def list_retrieval_test_results(
    test_set_id: str = Query(..., description="测试集ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取检索测试结果列表
    """
    # TODO: 实现获取检索测试结果逻辑
    return JSONResponse(
        content=page_response(
            data=[],
            total=0,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/retrieval/results/{result_id}", response_model=None, summary="获取检索测试结果详情")
async def get_retrieval_test_result(result_id: str):
    """
    获取单个检索测试结果的详细信息
    """
    # TODO: 实现获取检索测试结果详情逻辑
    return JSONResponse(
        content=success_response(
            data=None,
            message="检索测试结果详情（待实现）"
        )
    )


# ========== 生成测试 ==========

@router.post("/generation/run", response_model=None, summary="执行生成测试")
async def run_generation_test(data: RunGenerationTestRequest):
    """
    执行生成测试
    
    - **test_case_id**: 单个测试用例ID（单次测试）
    - **test_set_id**: 测试集ID（批量测试）
    - **llm_model**: 使用的LLM模型
    
    test_case_id 和 test_set_id 二选一
    """
    # TODO: 实现执行生成测试逻辑
    return JSONResponse(
        content=success_response(
            data={"task_id": "task_temp_001"},
            message="生成测试已启动（待实现）"
        )
    )


@router.get("/generation/results", response_model=None, summary="获取生成测试结果")
async def list_generation_test_results(
    test_set_id: str = Query(..., description="测试集ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取生成测试结果列表
    """
    # TODO: 实现获取生成测试结果逻辑
    return JSONResponse(
        content=page_response(
            data=[],
            total=0,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/generation/results/{result_id}", response_model=None, summary="获取生成测试结果详情")
async def get_generation_test_result(result_id: str):
    """
    获取单个生成测试结果的详细信息
    """
    # TODO: 实现获取生成测试结果详情逻辑
    return JSONResponse(
        content=success_response(
            data=None,
            message="生成测试结果详情（待实现）"
        )
    )

