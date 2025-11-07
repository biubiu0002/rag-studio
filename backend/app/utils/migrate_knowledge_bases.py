"""
知识库数据迁移工具
将现有的 knowledge_bases.json 迁移到 debug_results/knowledge_bases/
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from app.config import settings


def migrate_knowledge_bases():
    """
    迁移知识库数据从 knowledge_bases.json 到 debug_results/knowledge_bases/
    """
    storage_path = Path(settings.STORAGE_PATH)
    old_file = storage_path / "knowledge_bases.json"
    new_dir = storage_path / "debug_results" / "knowledge_bases"
    new_dir.mkdir(parents=True, exist_ok=True)
    index_file = new_dir / "_index.json"
    
    # 检查旧文件是否存在
    if not old_file.exists():
        print("未找到 knowledge_bases.json，无需迁移")
        return
    
    # 读取旧数据
    try:
        with open(old_file, "r", encoding="utf-8") as f:
            old_kbs = json.load(f)
    except Exception as e:
        print(f"读取 knowledge_bases.json 失败: {e}")
        return
    
    if not isinstance(old_kbs, list):
        print("knowledge_bases.json 格式错误，应为数组")
        return
    
    # 读取现有索引
    index_data = []
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        except Exception as e:
            print(f"读取索引文件失败: {e}")
    
    existing_ids = {item.get("id") for item in index_data}
    
    # 迁移每个知识库
    migrated_count = 0
    skipped_count = 0
    
    for kb_data in old_kbs:
        kb_id = kb_data.get("id")
        if not kb_id:
            print(f"跳过无效的知识库（缺少ID）: {kb_data.get('name', 'Unknown')}")
            skipped_count += 1
            continue
        
        # 检查是否已存在
        if kb_id in existing_ids:
            print(f"跳过已存在的知识库: {kb_id} ({kb_data.get('name', 'Unknown')})")
            skipped_count += 1
            continue
        
        # 构建新的配置格式
        config = {
            "id": kb_id,
            "name": kb_data.get("name", ""),
            "type": "knowledge_bases",
            "data": {
                **kb_data,
                "schema": {
                    "vector_db_type": kb_data.get("vector_db_type", "qdrant"),
                    "fields": [
                        {"name": "content", "type": "text", "isIndexed": True, "isVectorIndex": False},
                        {"name": "embedding", "type": "array", "isIndexed": True, "isVectorIndex": True}
                    ]
                }
            },
            "timestamp": int(datetime.now().timestamp() * 1000),
            "metadata": {
                "kb_id": kb_id,
                "kb_name": kb_data.get("name", ""),
                "vector_db_type": kb_data.get("vector_db_type", "qdrant"),
                "field_count": 2
            }
        }
        
        # 保存配置文件
        config_file = new_dir / f"{kb_id}.json"
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存知识库配置失败 {kb_id}: {e}")
            skipped_count += 1
            continue
        
        # 更新索引
        index_data.append({
            "id": kb_id,
            "name": kb_data.get("name", ""),
            "timestamp": config["timestamp"],
            "metadata": config["metadata"]
        })
        
        migrated_count += 1
        print(f"迁移知识库: {kb_id} ({kb_data.get('name', 'Unknown')})")
    
    # 保存索引（按时间戳倒序）
    index_data.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    try:
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存索引文件失败: {e}")
        return
    
    print(f"\n迁移完成:")
    print(f"  成功迁移: {migrated_count} 个知识库")
    print(f"  跳过: {skipped_count} 个知识库")
    print(f"\n新数据位置: {new_dir}")
    print(f"\n注意: 原文件 {old_file} 未被删除，请手动备份后删除")


if __name__ == "__main__":
    migrate_knowledge_bases()

