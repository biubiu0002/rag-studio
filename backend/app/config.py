"""
应用配置模块
使用 pydantic-settings 管理环境变量配置
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import os

# 获取项目根目录 (backend目录)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    APP_NAME: str = Field(default="RAG Studio Backend", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    DEBUG: bool = Field(default=True, description="调试模式")
    API_PREFIX: str = Field(default="/api/v1", description="API路径前缀")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器主机")
    PORT: int = Field(default=8000, description="服务器端口")
    
    # CORS配置
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001",
        description="允许的跨域源（逗号分隔）"
    )
    
    # 数据库配置
    DB_HOST: str = Field(default="localhost", description="数据库主机")
    DB_PORT: int = Field(default=3306, description="数据库端口")
    DB_USER: str = Field(default="root", description="数据库用户")
    DB_PASSWORD: str = Field(default="", description="数据库密码")
    DB_NAME: str = Field(default="rag_studio", description="数据库名称")
    
    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=5, description="连接池大小（保持的连接数）")
    DB_MAX_OVERFLOW: int = Field(default=10, description="连接池最大溢出连接数")
    DB_POOL_TIMEOUT: int = Field(default=30, description="获取连接的超时时间（秒）")
    DB_POOL_RECYCLE: int = Field(default=3600, description="连接回收时间（秒），超过此时间的连接会被回收")
    DB_POOL_PRE_PING: bool = Field(default=True, description="连接前是否执行ping检查，确保连接有效")
    
    # 存储配置
    STORAGE_TYPE: str = Field(default="json", description="存储类型: json 或 mysql")
    STORAGE_PATH: str = Field(default=os.path.join(PROJECT_ROOT, "storage"), description="JSON文件存储路径")
    
    # 模型配置
    MODELS_PATH: str = Field(default=os.path.join(PROJECT_ROOT, "resources", "models"), description="模型文件存储路径")
    BM25_MODEL_NAME: str = Field(default="bm25_zh_default.json", description="BM25模型文件名")
    BM25_MODEL_URL: str = Field(default="http://dashvector-data.oss-cn-beijing.aliyuncs.com/public/sparsevector/bm25_zh_default.json", description="BM25模型下载URL")
    
    # Ollama配置
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama服务地址")
    OLLAMA_EMBEDDING_MODEL: str = Field(default="nomic-embed-text", description="嵌入模型")
    OLLAMA_CHAT_MODEL: str = Field(default="deepseek-r1:1.5b", description="对话模型（确保模型在Ollama中存在，评估任务会使用任务配置中的llm_model）")
    
    # 自研服务配置（预留）
    CUSTOM_SERVICE_URL: str = Field(default="", description="自研服务地址")
    CUSTOM_SERVICE_API_KEY: str = Field(default="", description="自研服务API密钥")
    
    # 向量数据库配置
    VECTOR_DB_TYPE: str = Field(default="qdrant", description="向量数据库类型")
    
    # Elasticsearch配置
    ES_HOST: str = Field(default="localhost", description="ES主机")
    ES_PORT: int = Field(default=9200, description="ES端口")
    ES_USER: str = Field(default="", description="ES用户")
    ES_PASSWORD: str = Field(default="", description="ES密码")
    
    # Qdrant配置
    QDRANT_HOST: str = Field(default="localhost", description="Qdrant主机")
    QDRANT_PORT: int = Field(default=6333, description="Qdrant端口")
    QDRANT_API_KEY: str = Field(default="", description="Qdrant API密钥")
    
    # Milvus配置
    MILVUS_HOST: str = Field(default="localhost", description="Milvus主机")
    MILVUS_PORT: int = Field(default=19530, description="Milvus端口")
    MILVUS_USER: str = Field(default="", description="Milvus用户")
    MILVUS_PASSWORD: str = Field(default="", description="Milvus密码")
    
    # 任务执行器配置
    TASK_EXECUTOR_URL: str = Field(default="http://localhost:8001", description="任务执行器服务地址")
    TASK_NOTIFIER_TYPE: str = Field(default="http", description="任务通知器类型: http 或 mq")
    TASK_EXECUTOR_MAX_CONCURRENT: int = Field(default=5, description="任务执行器最大并发数")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """获取CORS允许的源列表"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        from urllib.parse import quote_plus
        # 对密码进行 URL 编码，避免特殊字符（如 @）导致解析错误
        encoded_password = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ""
        encoded_user = quote_plus(self.DB_USER) if self.DB_USER else ""
        return f"mysql+pymysql://{encoded_user}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    @property
    def elasticsearch_url(self) -> str:
        """获取Elasticsearch连接URL"""
        if self.ES_USER and self.ES_PASSWORD:
            return f"http://{self.ES_USER}:{self.ES_PASSWORD}@{self.ES_HOST}:{self.ES_PORT}"
        return f"http://{self.ES_HOST}:{self.ES_PORT}"


# 创建全局配置实例
settings = Settings()

