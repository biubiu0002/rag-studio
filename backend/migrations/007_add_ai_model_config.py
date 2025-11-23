"""
迁移脚本 007：为知识库添加AI模型配置字段
添加字段：embedding_endpoint, chat_provider, chat_model, chat_endpoint
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.database import SessionLocal


def migrate():
    """
    为knowledge_bases表添加AI模型配置相关字段
    
    新增字段：
    - embedding_endpoint: Embedding模型服务地址（可选）
    - chat_provider: Chat模型提供商（默认ollama）
    - chat_model: Chat模型名称（可选）
    - chat_endpoint: Chat模型服务地址（可选）
    """
    db = SessionLocal()
    
    try:
        # 获取当前表的列信息
        inspector = inspect(db.bind)
        columns = [col['name'] for col in inspector.get_columns('knowledge_bases')]
        
        print("当前knowledge_bases表中的列:", columns)
        
        # 检查并添加缺失的字段
        fields_to_add = [
            ('embedding_endpoint', "VARCHAR(500) NULL", "Embedding模型服务地址"),
            ('chat_provider', "VARCHAR(20) NOT NULL DEFAULT 'ollama'", "Chat模型提供商"),
            ('chat_model', "VARCHAR(100) NULL", "Chat模型名称"),
            ('chat_endpoint', "VARCHAR(500) NULL", "Chat模型服务地址"),
        ]
        
        added_count = 0
        for field_name, field_def, field_desc in fields_to_add:
            if field_name not in columns:
                print(f"添加字段 {field_name}（{field_desc}）...")
                db.execute(text(f"ALTER TABLE knowledge_bases ADD COLUMN {field_name} {field_def}"))
                added_count += 1
            else:
                print(f"字段 {field_name} 已存在，跳过")
        
        if added_count > 0:
            db.commit()
            print(f"迁移完成：共添加 {added_count} 个字段")
        else:
            print("所有字段已存在，无需迁移")
    
    except Exception as e:
        db.rollback()
        print(f"迁移失败: {e}")
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
