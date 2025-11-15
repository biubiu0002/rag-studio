"""
FastAPI应用主入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import setup_exception_handlers
from app.core.middleware import setup_middlewares


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动和关闭时执行的操作
    """
    # 启动时执行
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")
    print(f"📦 存储类型: {settings.STORAGE_TYPE}")
    print(f"🤖 AI服务: Ollama ({settings.OLLAMA_BASE_URL})")
    print(f"🗂️  向量数据库: {settings.VECTOR_DB_TYPE}")
    
    # 初始化存储目录
    if settings.STORAGE_TYPE == "json":
        import os
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        print(f"📁 JSON存储路径: {settings.STORAGE_PATH}")
    
    # 初始化模型
    print(f"\n🤖 初始化 AI 模型...")
    try:
        # 初始化 BM25 模型
        import os
        from app.services.sparse_vector_service import SparseVectorServiceFactory
        
        bm25_model_path = os.path.join(settings.MODELS_PATH, settings.BM25_MODEL_NAME)
        if os.path.exists(bm25_model_path):
            try:
                _ = SparseVectorServiceFactory.create('bm25', model_path=bm25_model_path)
                print(f"✅ BM25 模型初始化成功")
            except Exception as e:
                print(f"⚠️  BM25 模型初始化失败: {str(e)}")
                print(f"   应用仍可继续运行，但不能使用 BM25 功能")
        else:
            print(f"⚠️  BM25 模型文件不存在: {bm25_model_path}")
            print(f"   请运行脚本下载模型")
    except Exception as e:
        print(f"⚠️  模型初始化出错: {str(e)}")
    
    yield
    
    # 关闭时执行
    print(f"👋 {settings.APP_NAME} 正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="RAG管理平台后端API - 支持云边架构的知识库管理、链路排查和测试评估",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置自定义中间件
setup_middlewares(app)

# 设置异常处理器
setup_exception_handlers(app)


@app.get("/")
async def root():
    """根路径 - 健康检查"""
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "status": "healthy",
            "docs": f"{settings.API_PREFIX}/docs",
        }
    )


@app.get(f"{settings.API_PREFIX}/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "storage_type": settings.STORAGE_TYPE,
            "vector_db": settings.VECTOR_DB_TYPE,
        }
    )


# 导入并注册路由
from app.controllers import knowledge_base, document, test_management, pipeline, retriever_evaluation, debug_pipeline, evaluation
from app.controllers.new_test_management import retriever_router, generation_router

app.include_router(knowledge_base.router, prefix=settings.API_PREFIX)
app.include_router(document.router, prefix=settings.API_PREFIX)
app.include_router(test_management.router, prefix=settings.API_PREFIX)
app.include_router(pipeline.router, prefix=settings.API_PREFIX)
app.include_router(retriever_evaluation.router, prefix=settings.API_PREFIX)
app.include_router(debug_pipeline.router, prefix=settings.API_PREFIX)
app.include_router(evaluation.router, prefix=settings.API_PREFIX)

# 注册新的测试管理路由
app.include_router(retriever_router, prefix=settings.API_PREFIX)
app.include_router(generation_router, prefix=settings.API_PREFIX)


# 注意：不要直接运行此文件
# 请使用项目根目录的 run.py 或 uvicorn 命令启动
# 
# 正确的启动方式：
# 1. python run.py
# 2. uvicorn app.main:app --reload

