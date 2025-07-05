#!/usr/bin/env python3
"""
数据库迁移脚本：从旧的账号管理系统迁移到新的人设构建文档系统
删除旧的accounts表相关数据，创建新的persona_documents表
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.database import engine, get_db
from database.models import PersonaDocument
from sqlalchemy import text, inspect
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_table_exists(table_name):
    """检查表是否存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def drop_old_tables():
    """删除旧的账号管理相关表"""
    old_tables = [
        'accounts',  # 旧的账号表
    ]
    
    with engine.connect() as conn:
        for table_name in old_tables:
            if check_table_exists(table_name):
                try:
                    # SQLite不支持CASCADE，直接删除表
                    logger.info(f"正在删除表 {table_name}...")
                    conn.execute(text(f"DROP TABLE {table_name}"))
                    conn.commit()
                    logger.info(f"已删除表 {table_name}")
                except Exception as e:
                    logger.error(f"删除表 {table_name} 失败: {e}")
            else:
                logger.info(f"表 {table_name} 不存在，跳过删除")

def get_table_columns(table_name):
    """获取表的列信息"""
    inspector = inspect(engine)
    if table_name in inspector.get_table_names():
        return [col['name'] for col in inspector.get_columns(table_name)]
    return []

def update_foreign_key_tables():
    """更新包含外键引用的表（SQLite兼容版本）"""
    tables_to_update = ['contents', 'schedules', 'tasks', 'analytics']
    
    with engine.connect() as conn:
        for table_name in tables_to_update:
            if check_table_exists(table_name):
                logger.info(f"正在更新表 {table_name}...")
                columns = get_table_columns(table_name)
                
                # 添加account_name列（如果不存在）
                if 'account_name' not in columns:
                    try:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN account_name VARCHAR(100)"))
                        logger.info(f"已为表 {table_name} 添加 account_name 列")
                    except Exception as e:
                        logger.warning(f"添加account_name列失败: {e}")
                else:
                    logger.info(f"表 {table_name} 已有 account_name 列")
                
                # SQLite不支持直接删除列，但我们可以忽略account_id列
                # 在新系统中，我们只使用account_name
                if 'account_id' in columns:
                    logger.info(f"表 {table_name} 仍有 account_id 列，但在新系统中将被忽略")
                
                conn.commit()
                logger.info(f"表 {table_name} 更新完成")
            else:
                logger.info(f"表 {table_name} 不存在，跳过更新")

def create_new_tables():
    """创建新的人设文档表"""
    try:
        logger.info("正在创建新的人设文档表...")
        PersonaDocument.metadata.create_all(bind=engine)
        logger.info("人设文档表创建成功")
    except Exception as e:
        logger.error(f"创建人设文档表失败: {e}")
        raise

def verify_migration():
    """验证迁移结果"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # 检查新表是否创建
    if 'persona_documents' in tables:
        logger.info("✓ persona_documents 表已创建")
        
        # 检查表结构
        columns = [col['name'] for col in inspector.get_columns('persona_documents')]
        expected_columns = [
            'id', 'account_name', 'document_content', 'account_type', 
            'industry_field', 'platform', 'status', 'created_at', 
            'updated_at', 'completed_at', 'user_id', 'tags', 'summary'
        ]
        
        for col in expected_columns:
            if col in columns:
                logger.info(f"  ✓ 列 {col} 存在")
            else:
                logger.warning(f"  ✗ 列 {col} 不存在")
    else:
        logger.error("✗ persona_documents 表未创建")
    
    # 检查旧表是否删除
    if 'accounts' not in tables:
        logger.info("✓ 旧的 accounts 表已删除")
    else:
        logger.warning("✗ 旧的 accounts 表仍然存在")
    
    # 检查其他表的更新
    for table_name in ['contents', 'schedules', 'tasks', 'analytics']:
        if table_name in tables:
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            if 'account_name' in columns:
                logger.info(f"✓ 表 {table_name} 已添加 account_name 列")
            else:
                logger.warning(f"✗ 表 {table_name} 缺少 account_name 列")
            
            # SQLite不支持删除列，所以account_id列可能仍然存在，这是正常的
            if 'account_id' in columns:
                logger.info(f"ℹ 表 {table_name} 仍有 account_id 列（SQLite限制，但新系统将忽略此列）")
            else:
                logger.info(f"✓ 表 {table_name} 没有 account_id 列")

def main():
    """主迁移函数"""
    logger.info("开始数据库迁移...")
    
    try:
        # 1. 更新外键表结构
        logger.info("步骤 1: 更新外键表结构")
        update_foreign_key_tables()
        
        # 2. 删除旧表
        logger.info("步骤 2: 删除旧的账号管理表")
        drop_old_tables()
        
        # 3. 创建新表
        logger.info("步骤 3: 创建新的人设文档表")
        create_new_tables()
        
        # 4. 验证迁移
        logger.info("步骤 4: 验证迁移结果")
        verify_migration()
        
        logger.info("数据库迁移完成！")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 