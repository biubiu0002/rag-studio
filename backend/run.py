"""
应用启动脚本
从项目根目录启动，确保模块导入正确
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 地址: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API文档: http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}/docs")
    print(f"🔄 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )

