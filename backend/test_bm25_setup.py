"""
BM25 模型设置验证脚本
检查 BM25 模型下载和初始化是否正确
"""

import os
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """测试必要的导入"""
    print("\n" + "="*60)
    print("1️⃣  测试导入")
    print("="*60)
    
    try:
        from app.config import settings
        logger.info("✅ 成功导入 app.config.settings")
        
        from app.services.sparse_vector_service import (
            BM25SparseVectorService,
            SparseVectorServiceFactory,
            TFIDFSparseVectorService,
            SimpleSparseVectorService
        )
        logger.info("✅ 成功导入所有稀疏向量服务类")
        
        try:
            import dashtext
            logger.info("✅ dashtext 库已安装")
        except ImportError:
            logger.warning("⚠️  dashtext 库未安装，请运行: pip install dashtext")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print("\n" + "="*60)
    print("2️⃣  测试配置")
    print("="*60)
    
    try:
        from app.config import settings
        
        logger.info(f"模型存储路径: {settings.MODELS_PATH}")
        logger.info(f"BM25 模型名: {settings.BM25_MODEL_NAME}")
        logger.info(f"BM25 模型 URL: {settings.BM25_MODEL_URL}")
        
        # 检查目录是否存在
        models_path = Path(settings.MODELS_PATH)
        if models_path.exists():
            logger.info(f"✅ 模型目录存在")
        else:
            logger.warning(f"⚠️  模型目录不存在，将在首次运行时创建")
        
        return True
    except Exception as e:
        logger.error(f"❌ 配置读取失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_model_file():
    """测试模型文件"""
    print("\n" + "="*60)
    print("3️⃣  测试模型文件")
    print("="*60)
    
    try:
        from app.config import settings
        
        bm25_model_path = os.path.join(settings.MODELS_PATH, settings.BM25_MODEL_NAME)
        
        if os.path.exists(bm25_model_path):
            file_size = os.path.getsize(bm25_model_path) / (1024 * 1024)
            logger.info(f"✅ BM25 模型文件已存在")
            logger.info(f"   文件大小: {file_size:.2f} MB")
            return True
        else:
            logger.warning(f"⚠️  BM25 模型文件不存在: {bm25_model_path}")
            logger.info(f"   请运行以下命令下载模型:")
            logger.info(f"   python scripts/download_models.py")
            return False
    except Exception as e:
        logger.error(f"❌ 模型文件检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_bm25_service():
    """测试 BM25 服务"""
    print("\n" + "="*60)
    print("4️⃣  测试 BM25 服务")
    print("="*60)
    
    try:
        from app.config import settings
        from app.services.sparse_vector_service import SparseVectorServiceFactory
        
        bm25_model_path = os.path.join(settings.MODELS_PATH, settings.BM25_MODEL_NAME)
        
        if not os.path.exists(bm25_model_path):
            logger.warning(f"⚠️  模型文件不存在，跳过服务测试")
            return False
        
        # 创建服务实例
        logger.info("创建 BM25 服务实例...")
        service = SparseVectorServiceFactory.create('bm25', model_path=bm25_model_path)
        logger.info("✅ BM25 服务实例创建成功")
        
        # 测试单个文本
        logger.info("测试单个文本...")
        test_text = "这是一个测试文本"
        result = service.generate_sparse_vector(test_text)
        
        if result and isinstance(result, dict) and 'indices' in result and 'values' in result:
            logger.info(f"✅ 单个文本处理成功")
            logger.info(f"   向量长度: {len(result['indices'])}")
        else:
            logger.warning(f"⚠️  单个文本处理结果格式异常: {result}")
        
        # 测试多个文本
        logger.info("测试多个文本...")
        test_texts = ["第一个文本", "第二个文本", "第三个文本"]
        results = service.generate_sparse_vector(test_texts)
        
        if isinstance(results, list) and len(results) == 3:
            logger.info(f"✅ 多个文本处理成功")
            for i, result in enumerate(results):
                if isinstance(result, dict) and 'indices' in result and 'values' in result:
                    logger.info(f"   文本 {i+1}: 向量长度 {len(result['indices'])}")
        else:
            logger.warning(f"⚠️  多个文本处理结果异常")
        
        # 测试单例模式
        logger.info("测试单例模式...")
        service2 = SparseVectorServiceFactory.create('bm25', model_path=bm25_model_path)
        if service is service2:
            logger.info("✅ 单例模式正确（多次调用返回相同实例）")
        else:
            logger.warning("⚠️  单例模式异常")
        
        return True
        
    except FileNotFoundError as e:
        logger.warning(f"⚠️  模型文件不存在: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ BM25 服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_factory():
    """测试服务工厂"""
    print("\n" + "="*60)
    print("5️⃣  测试服务工厂")
    print("="*60)
    
    try:
        from app.services.sparse_vector_service import SparseVectorServiceFactory
        
        # 测试 TF-IDF
        logger.info("创建 TF-IDF 服务...")
        tfidf_service = SparseVectorServiceFactory.create('tf-idf')
        logger.info("✅ TF-IDF 服务创建成功")
        
        # 测试 Simple
        logger.info("创建 Simple 服务...")
        simple_service = SparseVectorServiceFactory.create('simple')
        logger.info("✅ Simple 服务创建成功")
        
        # 测试无效的服务类型
        logger.info("测试无效服务类型...")
        try:
            invalid_service = SparseVectorServiceFactory.create('invalid')
            logger.warning("⚠️  应该抛出异常，但没有抛出")
        except ValueError as e:
            logger.info(f"✅ 正确抛出异常: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 服务工厂测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  BM25 模型设置验证工具".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "导入测试": test_imports(),
        "配置测试": test_config(),
        "模型文件测试": test_model_file(),
        "BM25 服务测试": test_bm25_service(),
        "服务工厂测试": test_factory(),
    }
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试汇总")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有测试通过！BM25 模型已准备好使用")
    else:
        print("⚠️  部分测试未通过")
        print("\n建议:")
        print("1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("2. 下载 BM25 模型: python scripts/download_models.py")
        print("3. 重新运行此脚本验证")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
