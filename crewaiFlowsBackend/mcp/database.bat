"""
数据库操作MCP工具
用于读取和修改crewai_flows.db数据库，支持账号信息、内容策略、竞品分析等操作
"""
from typing import Any, Dict, List, Optional
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 初始化FastMCP服务器
mcp = FastMCP("database")

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "crewai_flows.db"

def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(str(DB_PATH))

def dict_factory(cursor, row):
    """将SQLite行转换为字典"""
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))

@mcp.tool()
async def read_user_account(account_id: str = None) -> str:
    """读取用户账号信息
    
    参数:
        account_id: 账号ID（可选，如果不提供则返回所有账号）
    """
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        if account_id:
            # 查询特定账号信息
            cursor.execute("""
                SELECT id, name, platform, account_id, followers, notes, engagement, 
                       status, bio, tags, target_audience, positioning, content_strategy,
                       created_at, last_updated
                FROM accounts 
                WHERE id = ? OR account_id = ?
            """, (account_id, account_id))
            
            account = cursor.fetchone()
            if account:
                # 安全解析JSON字段
                if account.get('tags'):
                    try:
                        account['tags'] = json.loads(account['tags'])
                    except:
                        account['tags'] = []
                
                for json_field in ['target_audience', 'positioning', 'content_strategy']:
                    if account.get(json_field):
                        try:
                            account[json_field] = json.loads(account[json_field])
                        except:
                            account[json_field] = {}
                
                conn.close()
                return json.dumps({
                    "status": "success",
                    "data": account,
                    "message": f"成功获取账号 {account_id} 的信息"
                }, ensure_ascii=False, indent=2)
            else:
                conn.close()
                return json.dumps({
                    "status": "not_found",
                    "message": f"未找到账号ID为 {account_id} 的账号信息"
                }, ensure_ascii=False, indent=2)
        else:
            # 查询所有账号信息
            cursor.execute("""
                SELECT id, name, platform, account_id, followers, notes, engagement, 
                       status, created_at, last_updated
                FROM accounts 
                ORDER BY created_at_timestamp DESC
            """)
            
            accounts = cursor.fetchall()
            conn.close()
            
            return json.dumps({
                "status": "success",
                "data": accounts,
                "count": len(accounts),
                "message": f"成功获取 {len(accounts)} 个账号信息"
            }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"读取账号信息时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)

@mcp.tool()
async def update_user_account(account_id: str, account_data: str) -> str:
    """更新用户账号信息
    
    参数:
        account_id: 账号ID
        account_data: 账号数据JSON字符串
    """
    try:
        # 解析JSON数据
        data = json.loads(account_data)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建更新SQL
        update_fields = []
        values = []
        
        # 允许更新的字段
        allowed_fields = ['name', 'platform', 'account_id', 'avatar', 'status', 
                         'followers', 'notes', 'engagement', 'avg_views', 'verified',
                         'content_count', 'bio', 'tags', 'target_audience', 
                         'positioning', 'content_strategy', 'monetization']
        
        for field in allowed_fields:
            if field in data:
                if field in ['tags', 'target_audience', 'positioning', 'content_strategy', 'monetization']:
                    # JSON字段需要序列化
                    update_fields.append(f"{field} = ?")
                    values.append(json.dumps(data[field], ensure_ascii=False))
                else:
                    update_fields.append(f"{field} = ?")
                    values.append(data[field])
        
        if update_fields:
            # 添加更新时间
            update_fields.append("last_updated = ?")
            update_fields.append("updated_at_timestamp = ?")
            values.append(datetime.now().strftime('%Y-%m-%d'))
            values.append(datetime.now())
            values.append(account_id)
            values.append(account_id)
            
            update_sql = f"""
                UPDATE accounts 
                SET {', '.join(update_fields)}
                WHERE id = ? OR account_id = ?
            """
            
            cursor.execute(update_sql, values)
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return json.dumps({
                    "status": "success",
                    "message": f"成功更新账号 {account_id} 的信息",
                    "updated_fields": list(data.keys())
                }, ensure_ascii=False, indent=2)
            else:
                conn.close()
                return json.dumps({
                    "status": "not_found",
                    "message": f"未找到账号ID为 {account_id} 的记录"
                }, ensure_ascii=False, indent=2)
        else:
            conn.close()
            return json.dumps({
                "status": "error",
                "message": "没有有效的更新字段"
            }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"更新账号信息时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)

@mcp.tool()
async def read_user_content_strategy(account_id: str = None) -> str:
    """读取用户内容策略
    
    参数:
        account_id: 账号ID（可选，如果不提供则返回所有内容）
    """
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        if account_id:
            # 查询特定账号的内容
            cursor.execute("""
                SELECT c.*, a.name as account_name, a.platform
                FROM contents c
                LEFT JOIN accounts a ON c.account_id = a.id
                WHERE c.account_id = ?
                ORDER BY c.created_at_timestamp DESC
                LIMIT 20
            """, (account_id,))
        else:
            # 查询所有内容
            cursor.execute("""
                SELECT c.*, a.name as account_name, a.platform
                FROM contents c
                LEFT JOIN accounts a ON c.account_id = a.id
                ORDER BY c.created_at_timestamp DESC
                LIMIT 50
            """)
        
        contents = cursor.fetchall()
        conn.close()
        
        return json.dumps({
            "status": "success",
            "data": contents,
            "count": len(contents),
            "message": f"成功获取 {len(contents)} 条内容策略数据"
        }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"读取内容策略时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)

@mcp.tool()
async def read_user_competitors(competitor_id: str = None) -> str:
    """读取用户竞品分析数据
    
    参数:
        competitor_id: 竞品ID（可选，如果不提供则返回所有竞品）
    """
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        if competitor_id:
            # 查询特定竞品信息
            cursor.execute("""
                SELECT * FROM competitors 
                WHERE id = ?
            """, (competitor_id,))
            
            competitor = cursor.fetchone()
            if competitor:
                # 安全解析JSON字段
                if competitor.get('tags'):
                    try:
                        competitor['tags'] = json.loads(competitor['tags'])
                    except:
                        competitor['tags'] = []
                
                # 获取竞品的笔记数据
                cursor.execute("""
                    SELECT * FROM competitor_notes 
                    WHERE competitor_id = ?
                    ORDER BY upload_time DESC
                    LIMIT 10
                """, (competitor_id,))
                
                notes = cursor.fetchall()
                competitor['recent_notes'] = notes
                
                conn.close()
                return json.dumps({
                    "status": "success",
                    "data": competitor,
                    "message": f"成功获取竞品 {competitor_id} 的详细信息"
                }, ensure_ascii=False, indent=2)
            else:
                conn.close()
                return json.dumps({
                    "status": "not_found",
                    "message": f"未找到竞品ID为 {competitor_id} 的信息"
                }, ensure_ascii=False, indent=2)
        else:
            # 查询所有竞品信息
            cursor.execute("""
                SELECT id, name, platform, tier, category, followers, explosion_rate,
                       last_update, analysis_count
                FROM competitors 
                ORDER BY created_at_timestamp DESC
            """)
            
            competitors = cursor.fetchall()
            conn.close()
            
            return json.dumps({
                "status": "success",
                "data": competitors,
                "count": len(competitors),
                "message": f"成功获取 {len(competitors)} 个竞品信息"
            }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"读取竞品数据时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)

@mcp.tool()
async def analyze_user_data(analysis_type: str, target_id: str = None) -> str:
    """分析用户数据并提供建议
    
    参数:
        analysis_type: 分析类型 (account, content, competitor, overall, analytics)
        target_id: 目标ID（账号ID、竞品ID等，可选）
    """
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        analysis_result = {
            "analysis_type": analysis_type,
            "target_id": target_id,
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "insights": [],
            "recommendations": []
        }
        
        if analysis_type == "account":
            # 账号分析
            if target_id:
                cursor.execute("SELECT * FROM accounts WHERE id = ?", (target_id,))
                account = cursor.fetchone()
                if account:
                    analysis_result["data"]["account"] = account
                    analysis_result["insights"].append(f"账号 {account['name']} 在 {account['platform']} 平台运营")
                    analysis_result["insights"].append(f"粉丝数: {account['followers']}, 互动率: {account['engagement']}%")
                    
                    # 基于数据给出建议
                    if account['engagement'] < 3.0:
                        analysis_result["recommendations"].append("互动率偏低，建议增加与粉丝的互动频率")
                    if account['followers'] < 10000:
                        analysis_result["recommendations"].append("粉丝基数较小，建议加强内容质量和发布频率")
            
        elif analysis_type == "content":
            # 内容分析
            cursor.execute("""
                SELECT c.*, a.name as account_name 
                FROM contents c 
                LEFT JOIN accounts a ON c.account_id = a.id
                ORDER BY c.created_at_timestamp DESC 
                LIMIT 20
            """)
            contents = cursor.fetchall()
            analysis_result["data"]["contents"] = contents
            analysis_result["insights"].append(f"共分析了 {len(contents)} 条内容")
            
            # 分析内容表现
            if contents:
                avg_likes = sum(c.get('likes', 0) for c in contents) / len(contents)
                analysis_result["insights"].append(f"平均点赞数: {avg_likes:.1f}")
                analysis_result["recommendations"].append("建议分析高赞内容的共同特点，复制成功模式")
        
        elif analysis_type == "competitor":
            # 竞品分析
            cursor.execute("SELECT * FROM competitors ORDER BY explosion_rate DESC LIMIT 5")
            competitors = cursor.fetchall()
            analysis_result["data"]["top_competitors"] = competitors
            
            if competitors:
                top_competitor = competitors[0]
                analysis_result["insights"].append(f"表现最佳的竞品: {top_competitor['name']}")
                analysis_result["insights"].append(f"爆款率: {top_competitor['explosion_rate']}%")
                analysis_result["recommendations"].append(f"建议深入研究 {top_competitor['name']} 的内容策略")
        
        elif analysis_type == "analytics":
            # 数据分析
            cursor.execute("""
                SELECT * FROM analytics 
                ORDER BY date DESC 
                LIMIT 30
            """)
            analytics = cursor.fetchall()
            analysis_result["data"]["analytics"] = analytics
            
            if analytics:
                total_views = sum(a.get('views', 0) for a in analytics)
                total_likes = sum(a.get('likes', 0) for a in analytics)
                analysis_result["insights"].append(f"近30天总浏览量: {total_views}")
                analysis_result["insights"].append(f"近30天总点赞数: {total_likes}")
                
                if total_views > 0:
                    engagement_rate = (total_likes / total_views) * 100
                    analysis_result["insights"].append(f"整体互动率: {engagement_rate:.2f}%")
        
        elif analysis_type == "overall":
            # 综合分析
            cursor.execute("SELECT COUNT(*) as count FROM accounts")
            account_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM contents")
            content_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM competitors")
            competitor_count = cursor.fetchone()['count']
            
            analysis_result["data"]["summary"] = {
                "accounts": account_count,
                "contents": content_count,
                "competitors": competitor_count
            }
            
            analysis_result["insights"].append(f"系统中共有 {account_count} 个账号")
            analysis_result["insights"].append(f"共发布 {content_count} 条内容")
            analysis_result["insights"].append(f"跟踪 {competitor_count} 个竞品")
            analysis_result["recommendations"].append("建议定期更新竞品分析，保持竞争优势")
        
        conn.close()
        
        return json.dumps({
            "status": "success",
            "analysis": analysis_result,
            "message": f"成功完成 {analysis_type} 类型的数据分析"
        }, ensure_ascii=False, indent=2)
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"分析数据时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 初始化并运行服务器
    mcp.run(transport='stdio') 