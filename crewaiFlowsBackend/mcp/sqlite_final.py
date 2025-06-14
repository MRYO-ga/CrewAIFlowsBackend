from typing import Any
import sqlite3
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("sqlite-final")

# 常量
DATABASE_PATH = Path(__file__).parent.parent / "crewai_flows.db"

def get_db_connection() -> sqlite3.Connection | None:
    """获取数据库连接"""
    try:
        if not DATABASE_PATH.exists():
            conn = sqlite3.connect(str(DATABASE_PATH))
            conn.close()
        
        conn = sqlite3.connect(str(DATABASE_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    except Exception:
        return None

def format_query_result(rows: list, columns: list) -> str:
    """格式化查询结果"""
    if not rows:
        return "查询无结果。"
    
    result = f"查询结果 ({len(rows)} 行):\n"
    result += " | ".join(columns) + "\n"
    result += "-" * min(80, len(" | ".join(columns)) + 10) + "\n"
    
    # 显示前10行
    for row in rows[:10]:
        values = [str(value) if value is not None else "NULL" for value in row]
        result += " | ".join(values) + "\n"
    
    if len(rows) > 10:
        result += f"... (还有 {len(rows) - 10} 行)"
    
    return result

@mcp.tool()
async def sqlite_list_tables() -> str:
    """列出数据库中的所有表。这是数据库操作的起点工具，用于了解数据库结构。
    
    使用场景：
    - 用户询问"有哪些表"或"数据库结构"
    - 开始任何数据库操作前了解可用表
    - 作为其他操作的第一步，确认表是否存在
    
    无需参数。返回格式化的表列表。"""
    conn = get_db_connection()
    
    if not conn:
        return "无法连接到数据库。"
    
    try:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = cursor.fetchall()
        conn.close()
        
        if not tables:
            return "数据库中没有表。"
        
        table_names = [row[0] for row in tables]
        return f"数据库包含 {len(table_names)} 个表:\n" + "\n".join(f"- {name}" for name in table_names)
        
    except Exception:
        conn.close()
        return "查询表列表时出错。"

@mcp.tool()
async def sqlite_describe_table(table_name: str) -> str:
    """获取指定表的详细结构信息，包括字段名、类型、约束等。在对表进行任何操作前必须使用此工具了解表结构。
    
    使用场景：
    - 在插入数据前，了解表的字段和类型要求
    - 用户询问特定表的结构
    - 执行复杂查询前了解表字段
    - 验证表是否存在
    
    参数：
        table_name (str): 要查询的表名，必须是存在的表名
    
    返回：表结构的详细描述，包括字段类型、主键、非空约束等信息。"""
    conn = get_db_connection()
    
    if not conn:
        return "无法连接到数据库。"
    
    try:
        cursor = conn.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        
        if not columns:
            return f"表 '{table_name}' 不存在。"
        
        result = f"表 '{table_name}' 的结构:\n"
        for col in columns:
            result += f"- {col['name']}: {col['type']}"
            if col['pk']:
                result += " (主键)"
            if col['notnull']:
                result += " (非空)"
            result += "\n"
        
        return result
        
    except Exception:
        conn.close()
        return f"查询表 '{table_name}' 结构时出错。"

@mcp.tool()
async def sqlite_query(sql: str) -> str:
    """执行SQL查询、更新、删除等语句。这是最通用的数据库操作工具，支持所有标准SQL语句。
    
    使用场景：
    - SELECT查询：检索数据、统计分析
    - UPDATE语句：修改现有记录
    - DELETE语句：删除记录
    - 复杂的连表查询和数据分析
    
    重要提醒：
    - 执行UPDATE/DELETE前建议先用SELECT确认要操作的数据
    - 对于简单的插入操作，优先使用sqlite_insert_data工具
    - SQL语句必须是有效的SQLite语法
    
    参数：
        sql (str): 要执行的SQL语句，必须是有效的SQLite语法
    
    返回：查询结果（SELECT）或操作影响的行数（INSERT/UPDATE/DELETE）。"""
    conn = get_db_connection()
    
    if not conn:
        return "无法连接到数据库。"
    
    try:
        cursor = conn.execute(sql)
        
        if sql.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            result = format_query_result(rows, columns)
        else:
            affected_rows = cursor.rowcount
            conn.commit()
            result = f"操作完成，影响 {affected_rows} 行。"
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        return f"SQL执行失败: {str(e)}"

@mcp.tool()
async def sqlite_insert_data(table_name: str, data: str) -> str:
    """向指定表插入新记录。data参数必须是有效的JSON字符串格式。
    
    关键要求：
    - data参数必须是JSON字符串，如：'{"name": "张三", "age": 25}'
    - 插入前必须先了解表结构，确保字段匹配
    - 字段名必须与表结构完全一致
    
    使用场景：
    - 添加新的用户、订单、记录等
    - 批量插入结构化数据
    - 只适用于简单的单表插入操作
    
    操作顺序：
    1. 首先使用sqlite_describe_table了解表结构
    2. 根据表结构构造正确的JSON数据
    3. 调用此工具插入数据
    
    参数：
        table_name (str): 目标表名，必须是已存在的表
        data (str): JSON格式的数据字符串，如 '{"column1": "value1", "column2": "value2"}'
    
    示例：
        table_name: "users"
        data: '{"name": "张三", "email": "zhangsan@example.com", "age": 25}'
    
    返回：插入操作的结果确认。"""
    conn = get_db_connection()
    
    if not conn:
        return "无法连接到数据库。"
    
    try:
        # 解析JSON数据
        data_dict = json.loads(data)
        
        # 构建INSERT语句
        columns = list(data_dict.keys())
        placeholders = ["?" for _ in columns]
        values = list(data_dict.values())
        
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        cursor = conn.execute(sql, values)
        conn.commit()
        conn.close()
        
        return f"成功向表 '{table_name}' 插入数据。"
        
    except json.JSONDecodeError:
        conn.close()
        return "数据格式错误，请提供有效的JSON格式。"
    except Exception as e:
        conn.close()
        return f"插入数据失败: {str(e)}"

@mcp.tool()
async def sqlite_get_schema() -> str:
    """获取数据库的完整架构信息，包括所有表和视图的创建语句。用于全面了解数据库结构。
    
    使用场景：
    - 用户询问完整的数据库架构
    - 需要了解表之间的关系和依赖
    - 数据库结构分析和文档生成
    - 作为复杂数据操作的准备步骤
    
    优势：
    - 一次性获取所有数据库对象信息
    - 包含完整的SQL创建语句
    - 便于理解数据库设计和结构
    
    无需参数。返回包含所有表和视图的详细架构信息。"""
    conn = get_db_connection()
    
    if not conn:
        return "无法连接到数据库。"
    
    try:
        # 获取所有表和视图
        cursor = conn.execute("""
            SELECT name, type, sql 
            FROM sqlite_master 
            WHERE type IN ('table', 'view') 
            ORDER BY type, name
        """)
        objects = cursor.fetchall()
        conn.close()
        
        if not objects:
            return "数据库中没有表或视图。"
        
        result = f"数据库架构 ({len(objects)} 个对象):\n\n"
        
        for obj in objects:
            result += f"📋 {obj['type'].upper()}: {obj['name']}\n"
            if obj['sql']:
                result += f"   创建语句: {obj['sql']}\n"
            result += "\n"
        
        return result
        
    except Exception:
        conn.close()
        return "获取数据库架构时出错。"

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio') 