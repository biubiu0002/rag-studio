"""
新的测试管理控制器
处理检索器和生成测试用例的独立管理API
"""

from typing import List
from fastapi import APIRouter, Query, Path
from fastapi.responses import JSONResponse

from app.schemas.test import (
    RetrieverTestCaseCreate,
    RetrieverTestCaseUpdate,
    RetrieverTestCaseResponse,
    RetrieverTestCaseBatchCreate,
    GenerationTestCaseCreate,
    GenerationTestCaseUpdate,
    GenerationTestCaseResponse,
    GenerationTestCaseBatchCreate,
    BatchDeleteRequest,
    BatchOperationResponse,
    ExpectedAnswerCreate,
)
from app.core.response import success_response, page_response, error_response
from app.core.exceptions import NotFoundException, BadRequestException
from app.services.new_test_service import RetrieverTestCaseService, GenerationTestCaseService
import logging

logger = logging.getLogger(__name__)

# 创建两个独立的路由器
retriever_router = APIRouter(prefix="/tests/retriever", tags=["检索器测试用例"])
generation_router = APIRouter(prefix="/tests/generation", tags=["生成测试用例"])


# ========== 检索器测试用例API ==========

@retriever_router.post("/cases", response_model=None, summary="创建检索器测试用例")
async def create_retriever_test_case(data: RetrieverTestCaseCreate):
    """
    创建检索器测试用例
    
    - **test_set_id**: 所属测试集ID
    - **question**: 问题文本
    - **expected_answers**: 期望答案列表（至少一个）
    - **metadata**: 用例元数据（可选）
    """
    try:
        service = RetrieverTestCaseService()
        test_case = await service.create_test_case(data)
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = RetrieverTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="检索器测试用例创建成功"
            )
        )
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"创建检索器测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"创建检索器测试用例失败: {str(e)}")
        )


@retriever_router.post("/cases/batch", response_model=None, summary="批量创建检索器测试用例")
async def batch_create_retriever_test_cases(data: RetrieverTestCaseBatchCreate):
    """
    批量创建检索器测试用例
    
    - **test_set_id**: 所属测试集ID
    - **cases**: 测试用例列表
    """
    try:
        service = RetrieverTestCaseService()
        success_count, failed_count, failed_records = await service.batch_create_test_cases(
            test_set_id=data.test_set_id,
            cases_data=data.cases
        )
        
        response_data = BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_items=failed_records
        )
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message=f"批量导入完成：成功{success_count}个，失败{failed_count}个"
            )
        )
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"批量创建检索器测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"批量创建检索器测试用例失败: {str(e)}")
        )


@retriever_router.get("/cases", response_model=None, summary="获取检索器测试用例列表")
async def list_retriever_test_cases(
    test_set_id: str = Query(..., description="测试集ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取检索器测试用例列表（分页）
    """
    try:
        service = RetrieverTestCaseService()
        cases, total = await service.list_test_cases(
            test_set_id=test_set_id,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应格式
        response_data = []
        for case in cases:
            case_dict = case.model_dump()
            response_data.append(RetrieverTestCaseResponse.model_validate(case_dict).model_dump())
        
        return JSONResponse(
            content=page_response(
                data=response_data,
                total=total,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        logger.error(f"获取检索器测试用例列表失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取检索器测试用例列表失败: {str(e)}")
        )


@retriever_router.get("/cases/{case_id}", response_model=None, summary="获取检索器测试用例详情")
async def get_retriever_test_case(
    case_id: str = Path(..., description="测试用例ID")
):
    """
    根据ID获取检索器测试用例详情
    """
    try:
        service = RetrieverTestCaseService()
        test_case = await service.get_test_case(case_id)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = RetrieverTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="获取测试用例详情成功"
            )
        )
    except Exception as e:
        logger.error(f"获取检索器测试用例详情失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取检索器测试用例详情失败: {str(e)}")
        )


@retriever_router.put("/cases/{case_id}", response_model=None, summary="更新检索器测试用例")
async def update_retriever_test_case(
    case_id: str = Path(..., description="测试用例ID"),
    data: RetrieverTestCaseUpdate = None
):
    """
    更新检索器测试用例
    """
    try:
        service = RetrieverTestCaseService()
        test_case = await service.update_test_case(case_id, data)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = RetrieverTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="测试用例更新成功"
            )
        )
    except Exception as e:
        logger.error(f"更新检索器测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"更新检索器测试用例失败: {str(e)}")
        )


@retriever_router.delete("/cases/{case_id}", response_model=None, summary="删除检索器测试用例")
async def delete_retriever_test_case(
    case_id: str = Path(..., description="测试用例ID")
):
    """
    删除检索器测试用例
    """
    try:
        service = RetrieverTestCaseService()
        deleted = await service.delete_test_case(case_id)
        
        if not deleted:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        return JSONResponse(
            content=success_response(
                data={"deleted": True},
                message="测试用例删除成功"
            )
        )
    except Exception as e:
        logger.error(f"删除检索器测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"删除检索器测试用例失败: {str(e)}")
        )


@retriever_router.delete("/cases/batch", response_model=None, summary="批量删除检索器测试用例")
async def batch_delete_retriever_test_cases(data: BatchDeleteRequest):
    """
    批量删除检索器测试用例
    """
    try:
        service = RetrieverTestCaseService()
        success_count, failed_count = await service.batch_delete_test_cases(data.case_ids)
        
        response_data = BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_items=[]
        )
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message=f"批量删除完成：成功{success_count}个，失败{failed_count}个"
            )
        )
    except Exception as e:
        logger.error(f"批量删除检索器测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"批量删除检索器测试用例失败: {str(e)}")
        )


@retriever_router.post("/cases/{case_id}/answers", response_model=None, summary="添加期望答案")
async def add_expected_answer(
    case_id: str = Path(..., description="测试用例ID"),
    data: ExpectedAnswerCreate = None
):
    """
    向检索器测试用例添加期望答案
    """
    try:
        service = RetrieverTestCaseService()
        test_case = await service.add_expected_answer(case_id, data)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = RetrieverTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="期望答案添加成功"
            )
        )
    except Exception as e:
        logger.error(f"添加期望答案失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"添加期望答案失败: {str(e)}")
        )


@retriever_router.put("/cases/{case_id}/answers/{answer_index}", response_model=None, summary="更新期望答案")
async def update_expected_answer(
    case_id: str = Path(..., description="测试用例ID"),
    answer_index: int = Path(..., description="答案索引", ge=0),
    data: ExpectedAnswerCreate = None
):
    """
    更新检索器测试用例的某个期望答案
    """
    try:
        service = RetrieverTestCaseService()
        test_case = await service.update_expected_answer(case_id, answer_index, data)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = RetrieverTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="期望答案更新成功"
            )
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"更新期望答案失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"更新期望答案失败: {str(e)}")
        )


@retriever_router.delete("/cases/{case_id}/answers/{answer_index}", response_model=None, summary="删除期望答案")
async def delete_expected_answer(
    case_id: str = Path(..., description="测试用例ID"),
    answer_index: int = Path(..., description="答案索引", ge=0)
):
    """
    删除检索器测试用例的某个期望答案
    """
    try:
        service = RetrieverTestCaseService()
        test_case = await service.delete_expected_answer(case_id, answer_index)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = RetrieverTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="期望答案删除成功"
            )
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"删除期望答案失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"删除期望答案失败: {str(e)}")
        )


# ========== 生成测试用例API ==========

@generation_router.post("/cases", response_model=None, summary="创建生成测试用例")
async def create_generation_test_case(data: GenerationTestCaseCreate):
    """
    创建生成测试用例
    
    - **test_set_id**: 所属测试集ID
    - **question**: 问题文本
    - **reference_answer**: 参考答案
    - **reference_contexts**: 参考上下文列表（可选）
    - **metadata**: 用例元数据（可选）
    """
    try:
        service = GenerationTestCaseService()
        test_case = await service.create_test_case(data)
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = GenerationTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="生成测试用例创建成功"
            )
        )
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"创建生成测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"创建生成测试用例失败: {str(e)}")
        )


@generation_router.post("/cases/batch", response_model=None, summary="批量创建生成测试用例")
async def batch_create_generation_test_cases(data: GenerationTestCaseBatchCreate):
    """
    批量创建生成测试用例
    
    - **test_set_id**: 所属测试集ID
    - **cases**: 测试用例列表
    """
    try:
        service = GenerationTestCaseService()
        success_count, failed_count, failed_records = await service.batch_create_test_cases(
            test_set_id=data.test_set_id,
            cases_data=data.cases
        )
        
        response_data = BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_items=failed_records
        )
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message=f"批量导入完成：成功{success_count}个，失败{failed_count}个"
            )
        )
    except NotFoundException as e:
        return JSONResponse(
            status_code=404,
            content=error_response(message=str(e))
        )
    except Exception as e:
        logger.error(f"批量创建生成测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"批量创建生成测试用例失败: {str(e)}")
        )


@generation_router.get("/cases", response_model=None, summary="获取生成测试用例列表")
async def list_generation_test_cases(
    test_set_id: str = Query(..., description="测试集ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """
    获取生成测试用例列表（分页）
    """
    try:
        service = GenerationTestCaseService()
        cases, total = await service.list_test_cases(
            test_set_id=test_set_id,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应格式
        response_data = []
        for case in cases:
            case_dict = case.model_dump()
            response_data.append(GenerationTestCaseResponse.model_validate(case_dict).model_dump())
        
        return JSONResponse(
            content=page_response(
                data=response_data,
                total=total,
                page=page,
                page_size=page_size,
            )
        )
    except Exception as e:
        logger.error(f"获取生成测试用例列表失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取生成测试用例列表失败: {str(e)}")
        )


@generation_router.get("/cases/{case_id}", response_model=None, summary="获取生成测试用例详情")
async def get_generation_test_case(
    case_id: str = Path(..., description="测试用例ID")
):
    """
    根据ID获取生成测试用例详情
    """
    try:
        service = GenerationTestCaseService()
        test_case = await service.get_test_case(case_id)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = GenerationTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="获取测试用例详情成功"
            )
        )
    except Exception as e:
        logger.error(f"获取生成测试用例详情失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"获取生成测试用例详情失败: {str(e)}")
        )


@generation_router.put("/cases/{case_id}", response_model=None, summary="更新生成测试用例")
async def update_generation_test_case(
    case_id: str = Path(..., description="测试用例ID"),
    data: GenerationTestCaseUpdate = None
):
    """
    更新生成测试用例
    """
    try:
        service = GenerationTestCaseService()
        test_case = await service.update_test_case(case_id, data)
        
        if not test_case:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        # 转换为响应格式
        test_case_dict = test_case.model_dump()
        response_data = GenerationTestCaseResponse.model_validate(test_case_dict)
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message="测试用例更新成功"
            )
        )
    except Exception as e:
        logger.error(f"更新生成测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"更新生成测试用例失败: {str(e)}")
        )


@generation_router.delete("/cases/{case_id}", response_model=None, summary="删除生成测试用例")
async def delete_generation_test_case(
    case_id: str = Path(..., description="测试用例ID")
):
    """
    删除生成测试用例
    """
    try:
        service = GenerationTestCaseService()
        deleted = await service.delete_test_case(case_id)
        
        if not deleted:
            return JSONResponse(
                status_code=404,
                content=error_response(message=f"测试用例不存在: {case_id}")
            )
        
        return JSONResponse(
            content=success_response(
                data={"deleted": True},
                message="测试用例删除成功"
            )
        )
    except Exception as e:
        logger.error(f"删除生成测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"删除生成测试用例失败: {str(e)}")
        )


@generation_router.delete("/cases/batch", response_model=None, summary="批量删除生成测试用例")
async def batch_delete_generation_test_cases(data: BatchDeleteRequest):
    """
    批量删除生成测试用例
    """
    try:
        service = GenerationTestCaseService()
        success_count, failed_count = await service.batch_delete_test_cases(data.case_ids)
        
        response_data = BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_items=[]
        )
        
        return JSONResponse(
            content=success_response(
                data=response_data.model_dump(),
                message=f"批量删除完成：成功{success_count}个，失败{failed_count}个"
            )
        )
    except Exception as e:
        logger.error(f"批量删除生成测试用例失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=error_response(message=f"批量删除生成测试用例失败: {str(e)}")
        )
