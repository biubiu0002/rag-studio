"""
应用启动脚本
从项目根目录启动，确保模块导入正确
"""

import uvicorn
import sys
import os
from app.config import settings


def ensure_models():
    """
    确保模型文件存在
    在应用启动前下载应用所需的模型
    """
    print("\n" + "="*60)
    print("🤖 检查且下载模型文件")
    print("="*60)
    
    try:
        # 负责模型管理的脚本
        from scripts.download_models import download_all_models
        
        # 准备模型配置
        model_config = {
            'bm25': {
                'name': settings.BM25_MODEL_NAME,
                'url': settings.BM25_MODEL_URL
            }
        }
        
        # 执行模型下载（下载前会检查是否已经存在）
        success = download_all_models(settings.MODELS_PATH, model_config)
        
        print("="*60 + "\n")
        
        return success
        
    except Exception as e:
        print(f"\n⚠️  模型下载出错: {str(e)}")
        print("应用仍可继续运行，但BM25模型功能不可用\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📁 工作目录: {os.getcwd()}")
    print()
    
    # 先下载应用所需的模型，失败也不影响应用启动
    ensure_models()
    
    print(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📍 地址: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API文档: http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}/docs")
    print(f"🔄 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        # reload=settings.DEBUG,
        log_level="info",
    )

