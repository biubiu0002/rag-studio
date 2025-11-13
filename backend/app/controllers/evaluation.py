"""
评估控制器
提供评估任务的创建、执行和查询接口
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from app.core.response import success_response, page_response
from app.models.evaluation import EvaluationType, EvaluationStatus
from app.services.evaluation_task import EvaluationTaskService
from app.schemas.test import TestSetCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["评估管理"])


# ========== 请求/响应模型 ==========

class CreateEvaluationTaskRequest(BaseModel):
    """创建评估任务请求"""
    test_set_id: str = Field(..., description="测试集ID")
    kb_id: str = Field(..., description="知识库ID")
    evaluation_type: str = Field(..., description="评估类型: retrieval, generation")
    task_name: Optional[str] = Field(None, description="任务名称")
    retrieval_config: Optional[Dict[str, Any]] = Field(None, description="检索配置")
    generation_config: Optional[Dict[str, Any]] = Field(None, description="生成配置")


class ExecuteEvaluationTaskRequest(BaseModel):
    """执行评估任务请求"""
    save_detailed_results: bool = Field(True, description="是否保存详细结果")


# ========== 评估任务管理 ==========

@router.post("/tasks", response_model=None, summary="创建评估任务")
async def create_evaluation_task(request: CreateEvaluationTaskRequest):
    """
    创建评估任务
    
    - **test_set_id**: 测试集ID
    - **evaluation_type**: 评估类型（retrieval/generation）
    - **retrieval_config**: 检索配置（可选）
    - **generation_config**: 生成配置（可选）
    """
    try:
        evaluation_service = EvaluationTaskService()
        
        # 转换评估类型
        eval_type = EvaluationType(request.evaluation_type)
        
        task = await evaluation_service.create_evaluation_task(
            test_set_id=request.test_set_id,
            kb_id=request.kb_id,
            evaluation_type=eval_type,
            retrieval_config=request.retrieval_config,
            generation_config=request.generation_config,
            task_name=request.task_name
        )
        
        return JSONResponse(
            content=success_response(
                data={
                    "id": task.id,
                    "test_set_id": task.test_set_id,
                    "kb_id": task.kb_id,
                    "evaluation_type": task.evaluation_type.value,
                    "task_name": task.task_name,
                    "status": task.status.value,
                    "total_cases": task.total_cases
                },
                message="评估任务创建成功"
            )
        )
        
    except Exception as e:
        logger.error(f"创建评估任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/tasks/{task_id}/execute", response_model=None, summary="执行评估任务")
async def execute_evaluation_task(
    task_id: str,
    request: Optional[ExecuteEvaluationTaskRequest] = None
):
    """
    执行评估任务
    
    注意：这是一个长时间运行的任务，建议使用异步任务队列
    """
    try:
        evaluation_service = EvaluationTaskService()
        
        save_detailed = True
        if request:
            save_detailed = request.save_detailed_results
        
        # 执行评估（这里会阻塞，实际应该使用后台任务）
        task = await evaluation_service.execute_evaluation_task(
            task_id=task_id,
            save_detailed_results=save_detailed
        )
        
        return JSONResponse(
            content=success_response(
                data={
                    "id": task.id,
                    "status": task.status.value,
                    "total_cases": task.total_cases,
                    "completed_cases": task.completed_cases,
                    "failed_cases": task.failed_cases,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                },
                message="评估任务执行完成"
            )
        )
        
    except Exception as e:
        logger.error(f"执行评估任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/tasks", response_model=None, summary="获取评估任务列表")
async def list_evaluation_tasks(
    test_set_id: Optional[str] = Query(None, description="测试集ID筛选"),
    kb_id: Optional[str] = Query(None, description="知识库ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """获取评估任务列表"""
    try:
        evaluation_service = EvaluationTaskService()
        
        status_enum = None
        if status:
            status_enum = EvaluationStatus(status)
        
        tasks, total = await evaluation_service.list_evaluation_tasks(
            test_set_id=test_set_id,
            kb_id=kb_id,
            status=status_enum,
            page=page,
            page_size=page_size
        )
        
        tasks_data = [{
            "id": task.id,
            "test_set_id": task.test_set_id,
            "kb_id": task.kb_id,
            "evaluation_type": task.evaluation_type.value,
            "task_name": task.task_name,
            "status": task.status.value,
            "total_cases": task.total_cases,
            "completed_cases": task.completed_cases,
            "failed_cases": task.failed_cases,
            "created_at": task.created_at.isoformat() if task.created_at else None
        } for task in tasks]
        
        return JSONResponse(
            content=page_response(
                data=tasks_data,
                total=total,
                page=page,
                page_size=page_size
            )
        )
        
    except Exception as e:
        logger.error(f"获取评估任务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=None, summary="获取评估任务详情")
async def get_evaluation_task(task_id: str):
    """获取评估任务详情"""
    try:
        evaluation_service = EvaluationTaskService()
        task = await evaluation_service.get_evaluation_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="评估任务不存在")
        
        return JSONResponse(
            content=success_response(
                data={
                    "id": task.id,
                    "test_set_id": task.test_set_id,
                    "kb_id": task.kb_id,
                    "evaluation_type": task.evaluation_type.value,
                    "task_name": task.task_name,
                    "status": task.status.value,
                    "retrieval_config": task.retrieval_config,
                    "generation_config": task.generation_config,
                    "total_cases": task.total_cases,
                    "completed_cases": task.completed_cases,
                    "failed_cases": task.failed_cases,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                },
                message="获取成功"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估任务详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ========== 评估结果查询 ==========

@router.get("/tasks/{task_id}/summary", response_model=None, summary="获取评估汇总")
async def get_evaluation_summary(task_id: str):
    """获取评估任务的汇总结果"""
    try:
        evaluation_service = EvaluationTaskService()
        summary = await evaluation_service.get_evaluation_summary(task_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="评估汇总不存在")
        
        return JSONResponse(
            content=success_response(
                data={
                    "id": summary.id,
                    "evaluation_task_id": summary.evaluation_task_id,
                    "overall_retrieval_metrics": summary.overall_retrieval_metrics,
                    "overall_ragas_retrieval_metrics": summary.overall_ragas_retrieval_metrics,
                    "overall_ragas_generation_metrics": summary.overall_ragas_generation_metrics,
                    "overall_ragas_score": summary.overall_ragas_score,
                    "metrics_distribution": summary.metrics_distribution
                },
                message="获取成功"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估汇总失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/tasks/{task_id}/results", response_model=None, summary="获取评估用例结果")
async def get_evaluation_case_results(
    task_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
):
    """获取评估任务的用例结果列表"""
    try:
        evaluation_service = EvaluationTaskService()
        results, total = await evaluation_service.get_evaluation_case_results(
            task_id=task_id,
            page=page,
            page_size=page_size
        )
        
        results_data = [{
            "id": result.id,
            "test_case_id": result.test_case_id,
            "query": result.query,
            "status": result.status.value,
            "retrieval_metrics": result.retrieval_metrics,
            "ragas_retrieval_metrics": result.ragas_retrieval_metrics,
            "ragas_generation_metrics": result.ragas_generation_metrics,
            "ragas_score": result.ragas_score,
            "error_message": result.error_message
        } for result in results]
        
        return JSONResponse(
            content=page_response(
                data=results_data,
                total=total,
                page=page,
                page_size=page_size
            )
        )
        
    except Exception as e:
        logger.error(f"获取评估用例结果失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/tasks/{task_id}/results/{result_id}", response_model=None, summary="获取评估用例结果详情")
async def get_evaluation_case_result_detail(task_id: str, result_id: str):
    """获取单个评估用例结果的详细信息"""
    try:
        from app.repositories.factory import RepositoryFactory
        case_result_repo = RepositoryFactory.create_evaluation_case_result_repository()
        
        result = await case_result_repo.get_by_id(result_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="评估结果不存在")
        
        if result.evaluation_task_id != task_id:
            raise HTTPException(status_code=400, detail="结果不属于该任务")
        
        return JSONResponse(
            content=success_response(
                data={
                    "id": result.id,
                    "evaluation_task_id": result.evaluation_task_id,
                    "test_case_id": result.test_case_id,
                    "query": result.query,
                    "retrieved_chunks": result.retrieved_chunks,
                    "generated_answer": result.generated_answer,
                    "retrieval_time": result.retrieval_time,
                    "generation_time": result.generation_time,
                    "retrieval_metrics": result.retrieval_metrics,
                    "ragas_retrieval_metrics": result.ragas_retrieval_metrics,
                    "ragas_generation_metrics": result.ragas_generation_metrics,
                    "ragas_score": result.ragas_score,
                    "status": result.status.value,
                    "error_message": result.error_message
                },
                message="获取成功"
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估用例结果详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

