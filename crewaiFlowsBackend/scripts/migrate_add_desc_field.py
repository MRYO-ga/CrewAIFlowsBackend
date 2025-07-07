#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为xhs_notes表添加desc字段
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from database.database import DATABASE_URL

def migrate_add_desc_field():
    """为xhs_notes表添加desc字段"""
    print("🔧 开始数据库迁移：为xhs_notes表添加desc字段")
    
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('xhs_notes') 
                WHERE name = 'desc'
            """))
            
            field_exists = result.fetchone()[0] > 0
            
            if field_exists:
                print("✅ desc字段已存在，跳过迁移")
                return
            
            # 添加desc字段
            print("📝 正在添加desc字段...")
            conn.execute(text("""
                ALTER TABLE xhs_notes 
                ADD COLUMN desc TEXT
            """))
            
            # 提交更改
            conn.commit()
            print("✅ 成功添加desc字段到xhs_notes表")
            
            # 验证字段是否添加成功
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('xhs_notes') 
                WHERE name = 'desc'
            """))
            
            if result.fetchone()[0] > 0:
                print("✅ 验证成功：desc字段已添加到xhs_notes表")
            else:
                print("❌ 验证失败：desc字段未成功添加")
                
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    migrate_add_desc_field() 