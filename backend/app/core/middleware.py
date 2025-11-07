"""
中间件模块
"""

import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    请求ID中间件
    为每个请求生成唯一ID，便于日志追踪
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    计时中间件
    记录每个请求的处理时间
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # 打印请求日志
        request_id = getattr(request.state, "request_id", "unknown")
        print(
            f"📝 [{request_id}] {request.method} {request.url.path} "
            f"- {response.status_code} - {process_time:.3f}s"
        )
        
        return response


def setup_middlewares(app: FastAPI) -> None:
    """
    设置自定义中间件
    
    Args:
        app: FastAPI应用实例
    """
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)

