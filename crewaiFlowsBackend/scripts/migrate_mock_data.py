#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本 - 将前端mock数据导入到数据库

使用方法:
python scripts/migrate_mock_data.py
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal, create_tables
from database.models import Account, Content, Competitor, Schedule, ChatMessage
from sqlalchemy.orm import Session

# 前端mock数据
MOCK_ACCOUNTS_DATA = [
    {
        'id': '1',
        'name': '学生党美妆日记',
        'platform': 'xiaohongshu',
        'account_id': 'xhs88661123',
        'avatar': 'https://picsum.photos/id/64/200/200',
        'status': 'active',
        'created_at': '2024-03-15',
        'last_updated': '2024-03-19',
        'followers': 23000,
        'notes': 42,
        'engagement': 5.2,
        'avg_views': 8500,
        'verified': False,
        'content_count': 4,
        'bio': '大二学生｜月生活费1500的美妆省钱秘籍｜每天分享平价好物和新手化妆教程｜关注我，一起变美不踩坑！',
        'tags': ['平价美妆', '护肤', '化妆教程'],
        'target_audience': {
            'ageRange': '18-25岁',
            'genderRatio': '女性85% 男性15%',
            'location': '一二线城市为主',
            'consumptionLevel': 3,
            'interests': ['平价美妆', '护肤', '化妆教程', '学生生活'],
            'buyingPreferences': ['性价比', '口碑', '颜值']
        },
        'positioning': {
            'style': ['清新自然', '专业权威', '温馨治愈'],
            'content': ['产品测评', '教程分享', '好物推荐'],
            'advantage': '专注学生党平价美妆，每月消费不超过300元，新手友好的化妆教程，真实测评不踩坑'
        },
        'content_strategy': {
            'frequency': '每周3-4次',
            'bestTime': '12:00-14:00, 19:00-21:00',
            'types': ['图文测评', '视频教程', '好物分享'],
            'hotTopics': ['平价替代', '学生党必备', '新手教程', '避坑指南']
        },
        'monetization': {
            'monthlyIncome': 3500,
            'brandCount': 8,
            'adPrice': 800,
            'cooperationTypes': ['产品测评', '好物推荐', '教程合作']
        }
    },
    {
        'id': '2',
        'name': '轻奢美妆分享',
        'platform': 'xiaohongshu',
        'account_id': 'xhs66778899',
        'avatar': 'https://picsum.photos/id/65/200/200',
        'status': 'active',
        'created_at': '2024-02-20',
        'last_updated': '2024-03-18',
        'followers': 58000,
        'notes': 86,
        'engagement': 7.3,
        'avg_views': 15200,
        'verified': True,
        'content_count': 2,
        'bio': '职场小姐姐｜分享轻奢美妆好物｜工作日通勤妆容｜周末约会妆容｜让你每天都精致',
        'tags': ['轻奢美妆', '职场妆容', '通勤'],
        'target_audience': {
            'ageRange': '25-35岁',
            'genderRatio': '女性92% 男性8%',
            'location': '一线城市为主',
            'consumptionLevel': 4,
            'interests': ['轻奢美妆', '职场妆容', '护肤', '时尚穿搭'],
            'buyingPreferences': ['品牌', '功效', '颜值', '口碑']
        },
        'positioning': {
            'style': ['时尚潮流', '专业权威', '精致优雅'],
            'content': ['好物推荐', '教程分享', '产品测评'],
            'advantage': '专注职场女性美妆需求，提供高性价比轻奢产品推荐，妆容实用且有品味'
        },
        'content_strategy': {
            'frequency': '每周4-5次',
            'bestTime': '08:00-09:00, 18:00-20:00',
            'types': ['轻奢好物', '妆容教程', '职场穿搭'],
            'hotTopics': ['职场妆容', '轻奢好物', '通勤穿搭', '约会妆容']
        },
        'monetization': {
            'monthlyIncome': 12000,
            'brandCount': 15,
            'adPrice': 2500,
            'cooperationTypes': ['品牌代言', '产品测评', '直播带货', '联名合作']
        }
    },
    {
        'id': '3',
        'name': '职场美妆笔记',
        'platform': 'douyin',
        'account_id': 'dy123456789',
        'avatar': 'https://picsum.photos/id/66/200/200',
        'status': 'inactive',
        'created_at': '2024-01-10',
        'last_updated': '2024-03-10',
        'followers': 12000,
        'notes': 28,
        'engagement': 3.8,
        'avg_views': 5600,
        'verified': False,
        'content_count': 2,
        'bio': '职场新人｜5分钟快手妆容｜平价好物分享｜让你通勤路上也能变美',
        'tags': ['快手妆容', '职场', '平价'],
        'target_audience': {
            'ageRange': '22-28岁',
            'genderRatio': '女性88% 男性12%',
            'location': '二三线城市为主',
            'consumptionLevel': 2,
            'interests': ['快手妆容', '平价美妆', '护肤', '职场生活'],
            'buyingPreferences': ['性价比', '实用性', '口碑']
        },
        'positioning': {
            'style': ['简约实用', '清新自然', '专业权威'],
            'content': ['教程分享', '产品测评', '好物推荐'],
            'advantage': '专注快速妆容，适合忙碌的职场新人，5分钟搞定精致妆容'
        },
        'content_strategy': {
            'frequency': '每周2-3次',
            'bestTime': '07:00-08:00, 19:00-21:00',
            'types': ['快手教程', '平价好物', '职场技巧'],
            'hotTopics': ['5分钟妆容', '职场新人', '平价好物', '通勤必备']
        },
        'monetization': {
            'monthlyIncome': 1800,
            'brandCount': 5,
            'adPrice': 500,
            'cooperationTypes': ['产品测评', '好物推荐']
        }
    }
]

# 内容数据
MOCK_CONTENTS_DATA = [
    {
        'id': '1',
        'title': '油皮必备！平价好用的控油散粉测评',
        'cover': 'https://picsum.photos/id/64/400/300',
        'description': '测评了5款百元以内的控油散粉，从定妆效果、持久度、性价比等多个维度进行对比，帮助油皮姐妹找到最适合的控油散粉。',
        'content': '大家好！今天给大家带来5款平价控油散粉的详细测评...',
        'category': 'review',
        'status': 'published',
        'published_at': '2024-03-15 12:00',
        'created_at': '2024-03-14 10:30',
        'platform': 'xiaohongshu',
        'account_id': '1',
        'stats': {
            'views': 15600,
            'likes': 2300,
            'comments': 158,
            'shares': 89,
            'favorites': 426
        },
        'tags': ['控油', '散粉', '测评', '平价', '油皮']
    },
    {
        'id': '2',
        'title': '新手化妆必看！手把手教你打造清透妆容',
        'cover': 'https://picsum.photos/id/65/400/300',
        'description': '从底妆、眼妆到唇妆，详细讲解每个步骤，新手也能轻松上手，打造自然清透的日常妆容。',
        'content': '新手姐妹们，今天教大家如何打造清透自然的日常妆容！...',
        'category': 'tutorial',
        'status': 'reviewing',
        'created_at': '2024-03-16 14:20',
        'platform': 'xiaohongshu',
        'account_id': '1',
        'stats': {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0, 'favorites': 0},
        'tags': ['新手', '化妆教程', '清透', '日常妆']
    },
    {
        'id': '3',
        'title': '学生党必看！10款平价彩妆产品推荐',
        'cover': 'https://picsum.photos/id/68/400/300',
        'description': '学生党不到100元就能打造完整妆容，这些平价彩妆产品你值得拥有，性价比超高！',
        'content': '学生党姐妹们！今天分享10款超平价的彩妆好物...',
        'category': 'recommendation',
        'status': 'draft',
        'created_at': '2024-03-17 09:15',
        'platform': 'xiaohongshu',
        'account_id': '1',
        'stats': {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0, 'favorites': 0},
        'tags': ['学生党', '平价', '彩妆', '推荐', '好物']
    },
    {
        'id': '4',
        'title': '职场通勤妆容分享｜简约大方又精致',
        'cover': 'https://picsum.photos/id/69/400/300',
        'description': '适合职场的日常通勤妆容，简单大方又不失精致，让你在职场中更加自信。',
        'content': '职场小姐姐们，今天分享一个简约大方的通勤妆容！...',
        'category': 'tutorial',
        'status': 'published',
        'published_at': '2024-03-12 08:00',
        'created_at': '2024-03-11 16:30',
        'platform': 'xiaohongshu',
        'account_id': '2',
        'stats': {
            'views': 12800,
            'likes': 1850,
            'comments': 123,
            'shares': 67,
            'favorites': 320
        },
        'tags': ['职场', '通勤', '妆容', '轻奢']
    },
    {
        'id': '5',
        'title': '5分钟快手妆容｜忙碌早晨的救星',
        'cover': 'https://picsum.photos/id/72/400/300',
        'description': '专为忙碌的职场新人设计的5分钟快手妆容，简单快速又有精神。',
        'content': '职场新人们，早上时间紧张？这个5分钟快手妆容拯救你！...',
        'category': 'tutorial',
        'status': 'published',
        'published_at': '2024-03-10 07:30',
        'created_at': '2024-03-09 20:15',
        'platform': 'douyin',
        'account_id': '3',
        'stats': {
            'views': 8900,
            'likes': 1200,
            'comments': 89,
            'shares': 45,
            'favorites': 156
        },
        'tags': ['快手妆容', '职场', '5分钟', '简单']
    }
]

# 竞品数据
MOCK_COMPETITORS_DATA = [
    {
        'id': '1',
        'name': '水北山南',
        'account_id': 'xhs88661123',
        'platform': 'xiaohongshu',
        'tier': 'top',
        'category': 'beauty_review',
        'followers': '128.6w',
        'explosion_rate': 12.7,
        'last_update': '2024-03-19',
        'analysis_count': 42,
        'avatar': 'https://picsum.photos/id/64/200/200',
        'profile_url': 'https://www.xiaohongshu.com/user/profile/水北山南',
        'tags': ['INFJ', '文字疗愈', '生活美学'],
        'analysis_document': '# 账号深度分析：水北山南（小红书）...'
    },
    {
        'id': '2',
        'name': '美妆情报局',
        'account_id': 'xhs77552211',
        'platform': 'xiaohongshu',
        'tier': 'top',
        'category': 'makeup_tutorial',
        'followers': '328.5w',
        'explosion_rate': 8.5,
        'last_update': '2024-03-18',
        'analysis_count': 35,
        'avatar': 'https://picsum.photos/id/65/200/200',
        'profile_url': 'https://www.xiaohongshu.com/user/profile/美妆情报局',
        'tags': ['测评', '种草', '美妆榜TOP5'],
        'analysis_document': '# 账号深度分析：美妆情报局（小红书）...'
    },
    {
        'id': '3',
        'name': '化妆师Lily',
        'account_id': 'xhs99887766',
        'platform': 'xiaohongshu',
        'tier': 'mid',
        'category': 'skincare_education',
        'followers': '215.3w',
        'explosion_rate': 6.3,
        'last_update': '2024-03-17',
        'analysis_count': 28,
        'avatar': 'https://picsum.photos/id/66/200/200',
        'profile_url': 'https://www.xiaohongshu.com/user/profile/化妆师Lily',
        'tags': ['教程', '新手', '美妆教程榜TOP3'],
        'analysis_document': '# 账号深度分析：化妆师Lily（小红书）...'
    }
]

def create_database():
    """创建数据库表"""
    print("正在创建数据库表...")
    create_tables()
    print("数据库表创建完成！")

def migrate_accounts(db: Session):
    """迁移账号数据"""
    print("正在迁移账号数据...")
    
    for account_data in MOCK_ACCOUNTS_DATA:
        # 检查是否已存在
        existing = db.query(Account).filter(Account.id == account_data['id']).first()
        if existing:
            print(f"账号 {account_data['name']} 已存在，跳过...")
            continue
            
        # 创建账号记录
        account = Account(
            id=account_data['id'],
            name=account_data['name'],
            platform=account_data['platform'],
            account_id=account_data['account_id'],
            avatar=account_data['avatar'],
            status=account_data['status'],
            created_at=account_data['created_at'],
            last_updated=account_data['last_updated'],
            followers=account_data['followers'],
            notes=account_data['notes'],
            engagement=account_data['engagement'],
            avg_views=account_data['avg_views'],
            verified=account_data['verified'],
            content_count=account_data['content_count'],
            bio=account_data['bio'],
            tags=account_data['tags'],
            target_audience=account_data['target_audience'],
            positioning=account_data['positioning'],
            content_strategy=account_data['content_strategy'],
            monetization=account_data['monetization']
        )
        
        db.add(account)
        print(f"已添加账号: {account_data['name']}")
    
    db.commit()
    print("账号数据迁移完成！")

def migrate_contents(db: Session):
    """迁移内容数据"""
    print("正在迁移内容数据...")
    
    for content_data in MOCK_CONTENTS_DATA:
        # 检查是否已存在
        existing = db.query(Content).filter(Content.id == content_data['id']).first()
        if existing:
            print(f"内容 {content_data['title']} 已存在，跳过...")
            continue
            
        # 创建内容记录
        content = Content(
            id=content_data['id'],
            title=content_data['title'],
            cover=content_data['cover'],
            description=content_data['description'],
            content=content_data['content'],
            category=content_data['category'],
            status=content_data['status'],
            published_at=content_data.get('published_at'),
            created_at=content_data['created_at'],
            scheduled_at=content_data.get('scheduled_at'),
            platform=content_data['platform'],
            account_id=content_data['account_id'],
            stats=content_data['stats'],
            tags=content_data['tags']
        )
        
        db.add(content)
        print(f"已添加内容: {content_data['title']}")
    
    db.commit()
    print("内容数据迁移完成！")

def migrate_competitors(db: Session):
    """迁移竞品数据"""
    print("正在迁移竞品数据...")
    
    for competitor_data in MOCK_COMPETITORS_DATA:
        # 检查是否已存在
        existing = db.query(Competitor).filter(Competitor.id == competitor_data['id']).first()
        if existing:
            print(f"竞品 {competitor_data['name']} 已存在，跳过...")
            continue
            
        # 创建竞品记录
        competitor = Competitor(
            id=competitor_data['id'],
            name=competitor_data['name'],
            account_id=competitor_data['account_id'],
            platform=competitor_data['platform'],
            tier=competitor_data['tier'],
            category=competitor_data['category'],
            followers=competitor_data['followers'],
            explosion_rate=competitor_data['explosion_rate'],
            last_update=competitor_data['last_update'],
            analysis_count=competitor_data['analysis_count'],
            avatar=competitor_data['avatar'],
            profile_url=competitor_data['profile_url'],
            tags=competitor_data['tags'],
            analysis_document=competitor_data['analysis_document']
        )
        
        db.add(competitor)
        print(f"已添加竞品: {competitor_data['name']}")
    
    db.commit()
    print("竞品数据迁移完成！")

def migrate_chat_messages(db: Session):
    """迁移聊天消息数据"""
    print("正在迁移聊天消息数据...")
    
    # 初始AI欢迎消息
    welcome_message = ChatMessage(
        id='welcome-1',
        content='👋 你好！我是SocialPulse AI，你的智能社交媒体运营助手。我可以帮你分析账号定位、拆解竞品、生成内容，还能管理多平台账号。',
        sender='ai',
        timestamp=datetime.now().isoformat(),
        status='received',
        user_id='default_user',
        session_id='default_session',
        intent='general_chat',
        references=[]
    )
    
    # 检查是否已存在
    existing = db.query(ChatMessage).filter(ChatMessage.id == 'welcome-1').first()
    if not existing:
        db.add(welcome_message)
        print("已添加欢迎消息")
    
    db.commit()
    print("聊天消息数据迁移完成！")

def main():
    """主函数"""
    print("开始执行数据迁移...")
    print("=" * 50)
    
    # 创建数据库表
    create_database()
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 执行数据迁移
        migrate_accounts(db)
        migrate_contents(db)
        migrate_competitors(db)
        migrate_chat_messages(db)
        
        print("=" * 50)
        print("✅ 数据迁移全部完成！")
        
        # 显示统计信息
        account_count = db.query(Account).count()
        content_count = db.query(Content).count()
        competitor_count = db.query(Competitor).count()
        message_count = db.query(ChatMessage).count()
        
        print(f"📊 数据统计:")
        print(f"  - 账号数量: {account_count}")
        print(f"  - 内容数量: {content_count}")
        print(f"  - 竞品数量: {competitor_count}")
        print(f"  - 聊天消息: {message_count}")
        
    except Exception as e:
        print(f"❌ 迁移过程中出现错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 