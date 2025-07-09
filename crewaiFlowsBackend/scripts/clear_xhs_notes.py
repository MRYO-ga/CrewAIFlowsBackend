#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理小红书笔记数据
"""
import sys
import os

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from sqlalchemy import create_engine, text
from database.database import DATABASE_URL

def clear_xhs_notes():
    """清理小红书笔记数据"""
    print("⚠️ 开始清理小红书笔记数据...")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 清理笔记数据
            result = conn.execute(text("DELETE FROM xhs_notes"))
            deleted_count = result.rowcount
            print(f"✅ 已删除 {deleted_count} 条笔记数据")
            
            # 重置自增ID（如果有的话）
            try:
                conn.execute(text("DELETE FROM sqlite_sequence WHERE name='xhs_notes'"))
                print("✅ 已重置自增ID")
            except Exception:
                # 如果不是SQLite或没有自增ID，忽略错误
                pass
            
            # 清理搜索记录
            try:
                result = conn.execute(text("DELETE FROM xhs_search_records"))
                deleted_count = result.rowcount
                print(f"✅ 已删除 {deleted_count} 条搜索记录")
            except Exception as e:
                print(f"⚠️ 删除搜索记录失败: {e}")
            
            # 清理API日志
            try:
                result = conn.execute(text("DELETE FROM xhs_api_logs"))
                deleted_count = result.rowcount
                print(f"✅ 已删除 {deleted_count} 条API日志")
            except Exception as e:
                print(f"⚠️ 删除API日志失败: {e}")
            
            conn.commit()
            print("✅ 数据清理完成")
    except Exception as e:
        print(f"❌ 清理数据失败: {e}")
        import traceback
        print(f"错误堆栈: {traceback.format_exc()}")

if __name__ == "__main__":
    clear_xhs_notes() 