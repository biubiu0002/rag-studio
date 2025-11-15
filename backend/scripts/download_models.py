"""
模型下载管理脚本
负责下载和管理必要的 AI 模型文件
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
import hashlib
import time

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_file(url: str, destination: str, max_retries: int = 3) -> bool:
    """
    下载文件
    
    Args:
        url: 文件下载地址
        destination: 本地保存路径
        max_retries: 最大重试次数
        
    Returns:
        是否下载成功
    """
    try:
        import httpx
    except ImportError:
        logger.error("httpx 库未安装，请运行 pip install httpx")
        return False
    
    # 确保目录存在
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"下载文件: {url}")
            logger.info(f"保存位置: {destination}")
            
            with httpx.stream('GET', url, timeout=300.0) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(destination, 'wb') as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 显示进度
                            if total_size:
                                progress = (downloaded / total_size) * 100
                                print(f"\r下载进度: {progress:.1f}% ({downloaded}/{total_size})", end='')
                
                print()  # 新行
                logger.info(f"✅ 文件下载成功: {destination}")
                return True
                
        except Exception as e:
            attempt_num = attempt + 1
            logger.warning(f"下载失败 (尝试 {attempt_num}/{max_retries}): {str(e)}")
            
            # 清理失败的下载文件
            if os.path.exists(destination):
                try:
                    os.remove(destination)
                except:
                    pass
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
    
    logger.error(f"❌ 文件下载失败，已尝试 {max_retries} 次: {url}")
    return False


def verify_file_integrity(file_path: str, expected_hash: Optional[str] = None) -> bool:
    """
    验证文件完整性
    
    Args:
        file_path: 文件路径
        expected_hash: 预期的 SHA256 哈希值
        
    Returns:
        文件是否完整
    """
    if not os.path.exists(file_path):
        return False
    
    try:
        file_size = os.path.getsize(file_path)
        logger.info(f"文件大小: {file_size / (1024*1024):.2f} MB")
        
        if expected_hash:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            
            file_hash = sha256_hash.hexdigest()
            if file_hash != expected_hash:
                logger.warning(f"文件哈希校验失败")
                logger.warning(f"预期: {expected_hash}")
                logger.warning(f"实际: {file_hash}")
                return False
            
            logger.info(f"✅ 文件哈希校验成功")
        
        return True
        
    except Exception as e:
        logger.error(f"验证文件时出错: {str(e)}")
        return False


def ensure_bm25_model(models_path: str, model_name: str, model_url: str) -> bool:
    """
    确保 BM25 模型文件存在
    
    Args:
        models_path: 模型存储目录
        model_name: 模型文件名
        model_url: 模型下载 URL
        
    Returns:
        模型是否可用
    """
    model_path = os.path.join(models_path, model_name)
    
    # 检查文件是否已存在
    if os.path.exists(model_path):
        logger.info(f"✅ BM25 模型文件已存在: {model_path}")
        
        # 验证文件完整性
        if verify_file_integrity(model_path):
            logger.info(f"✅ BM25 模型文件有效")
            return True
        else:
            logger.warning(f"BM25 模型文件无效，将重新下载")
            try:
                os.remove(model_path)
            except:
                pass
    
    # 下载模型
    logger.info(f"📥 开始下载 BM25 模型...")
    if not download_file(model_url, model_path):
        logger.error(f"❌ BM25 模型下载失败")
        return False
    
    # 验证下载的文件
    if verify_file_integrity(model_path):
        logger.info(f"✅ BM25 模型已就绪")
        return True
    else:
        logger.error(f"❌ 下载的 BM25 模型无效")
        return False


def download_all_models(models_path: str, model_config: dict) -> bool:
    """
    下载所有必要的模型
    
    Args:
        models_path: 模型存储目录
        model_config: 模型配置字典
        
    Returns:
        是否全部下载成功
    """
    os.makedirs(models_path, exist_ok=True)
    
    logger.info("=" * 50)
    logger.info("🤖 模型下载管理器")
    logger.info("=" * 50)
    logger.info(f"模型存储路径: {models_path}")
    logger.info("=" * 50)
    
    success = True
    
    # 下载 BM25 模型
    if 'bm25' in model_config:
        logger.info("\n📦 处理 BM25 模型...")
        bm25_config = model_config['bm25']
        if not ensure_bm25_model(
            models_path,
            bm25_config['name'],
            bm25_config['url']
        ):
            success = False
    
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("✅ 所有模型下载完成")
    else:
        logger.error("❌ 部分模型下载失败")
    logger.info("=" * 50)
    
    return success


def main():
    """主函数"""
    try:
        from app.config import settings
        
        # 准备模型配置
        model_config = {
            'bm25': {
                'name': settings.BM25_MODEL_NAME,
                'url': settings.BM25_MODEL_URL
            }
        }
        
        # 下载所有模型
        success = download_all_models(settings.MODELS_PATH, model_config)
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
