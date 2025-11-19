"""
将debug_results/knowledge_bases目录下的知识库数据迁移到标准存储位置
- 知识库基本信息 -> storage/knowledge_bases.json
- Schema配置 -> storage/knowledge_base_schemas/{kb_id}.json
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def load_kb_from_debug_file(file_path: Path) -> Dict[str, Any]:
    """从debug_results格式的文件中加载知识库数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        debug_data = json.load(f)
    
    # 提取知识库基本信息（从data字段）
    kb_data = debug_data.get("data", {})
    
    # 移除schema字段（单独存储）
    schema = kb_data.pop("schema", None)
    
    return {
        "kb_data": kb_data,
        "schema": schema
    }


def load_existing_kbs() -> List[Dict[str, Any]]:
    """加载现有的knowledge_bases.json"""
    kb_file = Path(settings.STORAGE_PATH) / "knowledge_bases.json"
    if kb_file.exists():
        with open(kb_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_kbs(kbs: List[Dict[str, Any]]) -> None:
    """保存知识库列表到knowledge_bases.json"""
    kb_file = Path(settings.STORAGE_PATH) / "knowledge_bases.json"
    kb_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(kb_file, "w", encoding="utf-8") as f:
        json.dump(kbs, f, ensure_ascii=False, indent=2)


def save_schema(kb_id: str, schema: Dict[str, Any]) -> None:
    """保存schema配置到knowledge_base_schemas/{kb_id}.json"""
    schema_dir = Path(settings.STORAGE_PATH) / "knowledge_base_schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    schema_file = schema_dir / f"{kb_id}.json"
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)


def migrate():
    """执行迁移"""
    debug_dir = Path(settings.STORAGE_PATH) / "debug_results" / "knowledge_bases"
    
    if not debug_dir.exists():
        print(f"❌ debug_results/knowledge_bases 目录不存在: {debug_dir}")
        return
    
    # 加载现有的知识库数据
    existing_kbs = load_existing_kbs()
    existing_ids = {kb["id"] for kb in existing_kbs}
    
    print(f"📦 现有知识库数量: {len(existing_kbs)}")
    print(f"📁 开始扫描: {debug_dir}")
    
    # 获取所有知识库配置文件（排除_index.json）
    kb_files = [f for f in debug_dir.glob("*.json") if f.name != "_index.json"]
    
    print(f"📄 找到 {len(kb_files)} 个知识库配置文件")
    
    migrated_count = 0
    skipped_count = 0
    schema_count = 0
    
    for kb_file in kb_files:
        try:
            # 加载知识库数据
            result = load_kb_from_debug_file(kb_file)
            kb_data = result["kb_data"]
            schema = result["schema"]
            
            kb_id = kb_data.get("id")
            if not kb_id:
                print(f"⚠️  跳过 {kb_file.name}：缺少ID")
                skipped_count += 1
                continue
            
            # 检查是否已存在
            if kb_id in existing_ids:
                print(f"⏭️  跳过 {kb_id}：已存在")
                skipped_count += 1
            else:
                # 添加到知识库列表
                existing_kbs.append(kb_data)
                existing_ids.add(kb_id)
                migrated_count += 1
                print(f"✓ 迁移知识库: {kb_id} ({kb_data.get('name', 'Unknown')})")
            
            # 保存schema配置（如果存在）
            if schema:
                save_schema(kb_id, schema)
                schema_count += 1
                print(f"  └─ 保存schema配置")
        
        except Exception as e:
            print(f"❌ 处理 {kb_file.name} 失败: {e}")
            skipped_count += 1
    
    # 保存更新后的知识库列表
    if migrated_count > 0:
        save_kbs(existing_kbs)
        print(f"\n✅ 迁移完成:")
        print(f"   - 新增知识库: {migrated_count}")
        print(f"   - 跳过已存在: {skipped_count}")
        print(f"   - 保存schema配置: {schema_count}")
        print(f"   - 总计知识库: {len(existing_kbs)}")
    else:
        print(f"\nℹ️  没有需要迁移的知识库")


if __name__ == "__main__":
    print("=" * 60)
    print("知识库数据迁移工具")
    print("从 debug_results/knowledge_bases 迁移到标准存储位置")
    print("=" * 60)
    print()
    
    migrate()

