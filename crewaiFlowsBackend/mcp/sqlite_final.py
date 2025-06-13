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
    """列出数据库中的所有表"""
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
    """获取表的结构信息
    
    参数:
        table_name: 表名
    """
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
    """执行SQL查询语句
    
    参数:
        sql: 要执行的SQL语句
    """
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
    """向表中插入数据
    
    参数:
        table_name: 表名
        data: JSON格式的数据，例如 {"name": "张三", "age": 25}
    """
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
    """获取数据库完整架构信息"""
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