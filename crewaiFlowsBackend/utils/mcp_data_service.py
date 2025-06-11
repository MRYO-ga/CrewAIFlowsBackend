"""
MCP数据服务模块 - 智能数据获取和管理系统
负责通过MCP协议获取用户的历史数据，包括账号信息、竞品分析、内容库、发布计划等
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPDataService:
    """MCP数据服务类 - 统一管理用户数据的获取和存储"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化MCP数据服务
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化数据库
        self.db_path = self.data_dir / "user_data.db"
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 账号基础信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    account_id TEXT UNIQUE,
                    platform TEXT DEFAULT 'xiaohongshu',
                    profile_data TEXT,  -- JSON格式存储
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 竞品分析数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS competitor_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    competitor_name TEXT NOT NULL,
                    competitor_id TEXT,
                    analysis_data TEXT,  -- JSON格式存储
                    analysis_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 内容库数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_library (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    content_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    content_type TEXT,  -- 'image_text', 'video', 'article'
                    status TEXT DEFAULT 'draft',  -- 'draft', 'published', 'scheduled'
                    content_data TEXT,  -- JSON格式存储
                    tags TEXT,  -- JSON数组格式
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 发布计划数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publish_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    schedule_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    schedule_type TEXT,  -- 'single', 'batch', 'ab_test', 'recurring'
                    status TEXT DEFAULT 'pending',
                    account_ids TEXT,  -- JSON数组格式
                    content_ids TEXT,  -- JSON数组格式
                    publish_time TIMESTAMP,
                    schedule_data TEXT,  -- JSON格式存储详细配置
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def get_account_info(self, user_id: str, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取账号基础信息
        
        Args:
            user_id: 用户ID
            account_id: 账号ID（可选，不提供则返回用户所有账号）
            
        Returns:
            Dict[str, Any]: 账号信息
        """
        return self._generate_mock_account_info(account_id)
    
    def get_competitor_analysis(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取竞品分析数据
        
        Args:
            user_id: 用户ID
            limit: 返回数据数量限制
            
        Returns:
            List[Dict[str, Any]]: 竞品分析数据列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT competitor_name, competitor_id, analysis_data, analysis_date
                FROM competitor_analysis 
                WHERE user_id = ?
                ORDER BY analysis_date DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            competitors = []
            for row in rows:
                competitors.append({
                    "competitor_name": row[0],
                    "competitor_id": row[1],
                    "analysis_data": json.loads(row[2] or "{}"),
                    "analysis_date": row[3]
                })
            
            if not competitors:
                # 如果没有数据，生成模拟竞品分析数据
                competitors = self._generate_mock_competitor_data()
            
            return competitors
    
    def get_content_library(self, user_id: str, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取内容库数据
        
        Args:
            user_id: 用户ID
            status: 内容状态过滤（可选）
            limit: 返回数据数量限制
            
        Returns:
            List[Dict[str, Any]]: 内容库数据列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT content_id, title, content_type, status, content_data, tags, created_at
                    FROM content_library 
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, status, limit))
            else:
                cursor.execute("""
                    SELECT content_id, title, content_type, status, content_data, tags, created_at
                    FROM content_library 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (user_id, limit))
            
            rows = cursor.fetchall()
            contents = []
            for row in rows:
                contents.append({
                    "content_id": row[0],
                    "title": row[1],
                    "content_type": row[2],
                    "status": row[3],
                    "content_data": json.loads(row[4] or "{}"),
                    "tags": json.loads(row[5] or "[]"),
                    "created_at": row[6]
                })
            
            if not contents:
                # 如果没有数据，生成模拟内容库数据
                contents = self._generate_mock_content_data()
            
            return contents
    
    def get_publish_schedule(self, user_id: str, status: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """
        获取发布计划数据
        
        Args:
            user_id: 用户ID
            status: 计划状态过滤（可选）
            limit: 返回数据数量限制
            
        Returns:
            List[Dict[str, Any]]: 发布计划数据列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute("""
                    SELECT schedule_id, title, schedule_type, status, publish_time, schedule_data
                    FROM publish_schedule 
                    WHERE user_id = ? AND status = ?
                    ORDER BY publish_time DESC
                    LIMIT ?
                """, (user_id, status, limit))
            else:
                cursor.execute("""
                    SELECT schedule_id, title, schedule_type, status, publish_time, schedule_data
                    FROM publish_schedule 
                    WHERE user_id = ?
                    ORDER BY publish_time DESC
                    LIMIT ?
                """, (user_id, limit))
            
            rows = cursor.fetchall()
            schedules = []
            for row in rows:
                schedules.append({
                    "schedule_id": row[0],
                    "title": row[1],
                    "schedule_type": row[2],
                    "status": row[3],
                    "publish_time": row[4],
                    "schedule_data": json.loads(row[5] or "{}")
                })
            
            if not schedules:
                # 如果没有数据，生成模拟发布计划数据
                schedules = self._generate_mock_schedule_data()
            
            return schedules
    
    def save_account_info(self, user_id: str, account_data: Dict[str, Any]) -> bool:
        """
        保存账号信息
        
        Args:
            user_id: 用户ID
            account_data: 账号数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO account_info 
                    (user_id, account_name, account_id, platform, profile_data, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    account_data.get("account_name", ""),
                    account_data.get("account_id", ""),
                    account_data.get("platform", "xiaohongshu"),
                    json.dumps(account_data.get("profile_data", {}), ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                logger.info(f"账号信息已保存: {account_data.get('account_name')}")
                return True
        except Exception as e:
            logger.error(f"保存账号信息失败: {e}")
            return False
    
    def _generate_mock_account_info(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """生成模拟账号信息"""
        return {
            "account_name": "美妆小达人",
            "account_id": account_id or "xhs123456789",
            "platform": "xiaohongshu",
            "profile_data": {
                "bio": "分享美妆心得，让每个女孩都能美美哒✨",
                "followers_count": 15800,
                "following_count": 892,
                "notes_count": 156,
                "likes_total": 89200,
                "profile_tags": ["美妆博主", "护肤达人", "学生党"],
                "avatar_url": "https://picsum.photos/id/64/200/200"
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _generate_mock_competitor_data(self) -> List[Dict[str, Any]]:
        """生成模拟竞品分析数据"""
        return [
            {
                "competitor_name": "水北山南",
                "competitor_id": "xhs88661123",
                "analysis_data": {
                    "followers": "128.6w",
                    "category": "文艺美妆",
                    "content_strategy": "文字疗愈+产品测评",
                    "posting_frequency": "每周2-3次",
                    "engagement_rate": 12.7,
                    "strengths": ["内容有深度", "文字功底强", "粉丝黏性高"],
                    "weaknesses": ["更新频率偏低", "商业化程度不高"],
                    "key_insights": "适合学习其文字表达技巧和情感共鸣能力"
                },
                "analysis_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            },
            {
                "competitor_name": "美妆情报局",
                "competitor_id": "xhs77552211",
                "analysis_data": {
                    "followers": "328.5w",
                    "category": "美妆测评",
                    "content_strategy": "专业测评+种草推荐",
                    "posting_frequency": "每周4-5次",
                    "engagement_rate": 8.5,
                    "strengths": ["专业性强", "测评详细", "更新稳定"],
                    "weaknesses": ["内容同质化", "缺乏个人特色"],
                    "key_insights": "可学习其测评方法和内容结构"
                },
                "analysis_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
            }
        ]
    
    def _generate_mock_content_data(self) -> List[Dict[str, Any]]:
        """生成模拟内容库数据"""
        return [
            {
                "content_id": "content_001",
                "title": "平价控油散粉测评｜学生党必看",
                "content_type": "image_text",
                "status": "draft",
                "content_data": {
                    "description": "测试了5款平价控油散粉，找到了最适合油皮学生党的宝藏产品！",
                    "images": ["image1.jpg", "image2.jpg", "image3.jpg"],
                    "tags": ["美妆测评", "平价好物", "控油散粉", "学生党"],
                    "target_keywords": ["平价", "控油", "散粉", "学生党"],
                    "estimated_views": 3500,
                    "optimization_suggestions": [
                        "标题可以加上具体价格范围",
                        "增加对比图表",
                        "添加使用心得"
                    ]
                },
                "tags": ["美妆", "测评", "平价"],
                "created_at": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "content_id": "content_002",
                "title": "新手化妆教程｜5分钟打造清透妆容",
                "content_type": "video",
                "status": "scheduled",
                "content_data": {
                    "description": "超详细的新手化妆教程，只需要5分钟就能画出清透自然的妆容！",
                    "video_duration": "06:32",
                    "tags": ["化妆教程", "新手向", "清透妆", "日常妆"],
                    "target_keywords": ["新手", "化妆", "教程", "清透"],
                    "estimated_views": 8000,
                    "optimization_suggestions": [
                        "可以制作分步骤的图文版本",
                        "添加产品清单",
                        "增加常见问题解答"
                    ]
                },
                "tags": ["教程", "化妆", "新手"],
                "created_at": (datetime.now() - timedelta(days=4)).isoformat()
            }
        ]
    
    def _generate_mock_schedule_data(self) -> List[Dict[str, Any]]:
        """生成模拟发布计划数据"""
        return [
            {
                "schedule_id": "schedule_001",
                "title": "春季护肤专题发布计划",
                "schedule_type": "batch",
                "status": "pending",
                "publish_time": (datetime.now() + timedelta(days=2)).isoformat(),
                "schedule_data": {
                    "account_ids": ["xhs123456789"],
                    "content_ids": ["content_001", "content_003"],
                    "description": "针对春季护肤需求的专题内容发布",
                    "target_metrics": {
                        "expected_views": 10000,
                        "expected_engagement_rate": 5.0
                    }
                }
            },
            {
                "schedule_id": "schedule_002",
                "title": "A/B测试：不同标题效果对比",
                "schedule_type": "ab_test",
                "status": "running",
                "publish_time": (datetime.now() - timedelta(days=1)).isoformat(),
                "schedule_data": {
                    "test_config": {
                        "duration": 48,
                        "variants": [
                            {"title": "平价控油散粉测评｜学生党必看", "account_id": "xhs123456789"},
                            {"title": "5款平价散粉横评｜哪款最控油？", "account_id": "xhs987654321"}
                        ]
                    },
                    "metrics": ["views", "likes", "comments", "engagement_rate"],
                    "current_results": {
                        "variant_a": {"views": 2800, "likes": 156, "comments": 23},
                        "variant_b": {"views": 3200, "likes": 189, "comments": 31}
                    }
                }
            }
        ]
    
    def get_user_context_data(self, user_id: str, data_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取用户的完整上下文数据，用于AI智能分析
        
        Args:
            user_id: 用户ID
            data_types: 需要获取的数据类型列表，如果为None则获取所有类型
            
        Returns:
            Dict[str, Any]: 用户的完整上下文数据
        """
        if data_types is None:
            data_types = ["account_info", "competitor_analysis", "content_library", "publish_schedule"]
        
        context_data = {}
        
        if "account_info" in data_types:
            context_data["account_info"] = self.get_account_info(user_id)
        
        if "competitor_analysis" in data_types:
            context_data["competitor_analysis"] = self.get_competitor_analysis(user_id)
        
        if "content_library" in data_types:
            context_data["content_library"] = self.get_content_library(user_id)
        
        if "publish_schedule" in data_types:
            context_data["publish_schedule"] = self.get_publish_schedule(user_id)
        
        return context_data

# 全局实例
mcp_data_service = MCPDataService() 