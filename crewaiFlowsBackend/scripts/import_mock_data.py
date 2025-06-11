# 导入前端mock数据到后端数据库
import sys
import os
import json
from datetime import datetime, timedelta
import uuid

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Account, Content, Competitor, Task, Schedule, ChatMessage, CompetitorNote, SOP, SOPCycle, SOPWeek, SOPTask, SOPTaskItem

def clean_database(db: Session):
    """清空数据库中的现有数据"""
    print("正在清空现有数据...")
    
    # 按依赖关系顺序删除
    db.query(Task).delete()
    db.query(Schedule).delete()
    db.query(Content).delete()
    db.query(ChatMessage).delete()
    db.query(CompetitorNote).delete()  # 新增：清空竞品笔记数据
    db.query(Competitor).delete()
    db.query(Account).delete()
    # SOP相关表
    db.query(SOPTaskItem).delete()
    db.query(SOPTask).delete()
    db.query(SOPWeek).delete()
    db.query(SOPCycle).delete()
    db.query(SOP).delete()
    
    db.commit()
    print("现有数据已清空！")

def import_accounts(db: Session):
    """导入账号数据"""
    print("正在导入账号数据...")
    
    accounts_data = [
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
    
    for account_data in accounts_data:
        account = Account(**account_data)
        db.add(account)
    
    db.commit()
    print(f"已导入 {len(accounts_data)} 个账号")

def import_contents(db: Session):
    """导入内容数据"""
    print("正在导入内容数据...")
    
    contents_data = [
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
                'favorites': 426,
                'engagement_rate': 16.8,
                'analysis': {
                    'performance_analysis': {
                        'peak_time': '2024-03-15 14:00',
                        'engagement_timeline': [
                            {'hour': 12, 'views': 2340, 'likes': 345},
                            {'hour': 13, 'views': 4560, 'likes': 678},
                            {'hour': 14, 'views': 6890, 'likes': 1023},
                            {'hour': 19, 'views': 3210, 'likes': 254}
                        ]
                    },
                    'audience_analysis': {
                        'age_distribution': {'18-22': 35, '23-27': 40, '28-32': 20, '33+': 5},
                        'gender_distribution': {'female': 92, 'male': 8},
                        'location_top5': ['上海', '北京', '广州', '深圳', '杭州'],
                        'device_type': {'mobile': 85, 'desktop': 15}
                    },
                    'content_analysis': {
                        'hot_keywords': ['控油', '平价', '散粉', '学生党', '性价比'],
                        'comment_sentiment': {'positive': 78, 'neutral': 18, 'negative': 4},
                        'top_comments': [
                            '这个测评太实用了！马上去买',
                            '学生党的福音，终于找到便宜好用的了',
                            '楼主测评很客观，关注了'
                        ],
                        'improvement_suggestions': [
                            '可以增加更多肤质的测试对比',
                            '建议添加持妆时长测试',
                            '可以做价格梯度的产品推荐'
                        ]
                    }
                }
            },
            'tags': ['控油', '散粉', '测评', '平价', '油皮']
        },
        {
            'id': '2',
            'title': '新手化妆必看！手把手教你打造清透妆容',
            'cover': 'https://picsum.photos/id/65/400/300',
            'description': '从底妆、眼妆到唇妆，详细讲解每个步骤，新手也能轻松上手，打造自然清透的日常妆容。',
            'content': '新手姐妹们，今天教大家如何打造清透自然的日常妆容！',
            'category': 'tutorial',
            'status': 'reviewing',
            'created_at': '2024-03-16 14:20',
            'platform': 'xiaohongshu',
            'account_id': '1',
            'stats': {
                'views': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'favorites': 0
            },
            'tags': ['新手', '化妆教程', '清透', '日常妆']
        },
        {
            'id': '3',
            'title': '学生党必看！10款平价彩妆产品推荐',
            'cover': 'https://picsum.photos/id/68/400/300',
            'description': '学生党不到100元就能打造完整妆容，这些平价彩妆产品你值得拥有，性价比超高！',
            'content': '学生党姐妹们！今天分享10款超平价的彩妆好物，总价不到100元就能拥有完整妆容！',
            'category': 'recommendation',
            'status': 'draft',
            'created_at': '2024-03-17 09:15',
            'platform': 'xiaohongshu',
            'account_id': '1',
            'stats': {
                'views': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'favorites': 0
            },
            'tags': ['学生党', '平价', '彩妆', '推荐', '好物']
        },
        {
            'id': '4',
            'title': '护肤小白必看！建立正确护肤步骤',
            'cover': 'https://picsum.photos/id/70/400/300',
            'description': '护肤新手容易踩坑，这篇文章教你建立正确的护肤步骤，避免常见误区。',
            'content': '护肤小白们，今天来聊聊正确的护肤步骤！',
            'category': 'knowledge',
            'status': 'scheduled',
            'scheduled_at': '2024-03-20 19:00',
            'created_at': '2024-03-18 11:45',
            'platform': 'xiaohongshu',
            'account_id': '1',
            'stats': {
                'views': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'favorites': 0
            },
            'tags': ['护肤', '新手', '步骤', '科普']
        },
        {
            'id': '5',
            'title': '职场通勤妆容分享｜简约大方又精致',
            'cover': 'https://picsum.photos/id/69/400/300',
            'description': '适合职场的日常通勤妆容，简单大方又不失精致，让你在职场中更加自信。',
            'content': '职场小姐姐们，今天分享一个简约大方的通勤妆容！',
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
                'favorites': 320,
                'engagement_rate': 15.2,
                'analysis': {
                    'performance_analysis': {
                        'peak_time': '2024-03-12 08:30',
                        'engagement_timeline': [
                            {'hour': 8, 'views': 3420, 'likes': 512},
                            {'hour': 9, 'views': 2890, 'likes': 433},
                            {'hour': 18, 'views': 4560, 'likes': 684},
                            {'hour': 19, 'views': 1930, 'likes': 221}
                        ]
                    },
                    'audience_analysis': {
                        'age_distribution': {'22-26': 45, '27-31': 35, '32-36': 15, '37+': 5},
                        'gender_distribution': {'female': 94, 'male': 6},
                        'location_top5': ['北京', '上海', '深圳', '杭州', '成都'],
                        'occupation': {'白领': 65, '学生': 20, '其他': 15}
                    },
                    'content_analysis': {
                        'hot_keywords': ['通勤妆', '职场', '简约', '精致', '轻奢'],
                        'comment_sentiment': {'positive': 85, 'neutral': 12, 'negative': 3},
                        'top_comments': [
                            '适合上班族的妆容，很实用',
                            '轻奢但不夸张，很有品味',
                            '步骤清晰，学会了！'
                        ],
                        'improvement_suggestions': [
                            '可以针对不同肤色做调整',
                            '建议增加产品价格信息',
                            '可以制作视频版教程'
                        ]
                    }
                }
            },
            'tags': ['职场', '通勤', '妆容', '轻奢']
        },
        {
            'id': '6',
            'title': '轻奢美妆好物分享｜值得投资的彩妆单品',
            'cover': 'https://picsum.photos/id/71/400/300',
            'description': '分享几款值得投资的轻奢彩妆单品，品质和效果都很出色，适合有一定预算的姐妹。',
            'content': '今天给大家分享几款值得投资的轻奢彩妆单品！',
            'category': 'recommendation',
            'status': 'draft',
            'created_at': '2024-03-18 14:20',
            'platform': 'xiaohongshu',
            'account_id': '2',
            'stats': {
                'views': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'favorites': 0
            },
            'tags': ['轻奢', '好物', '推荐', '投资']
        },
        {
            'id': '7',
            'title': '5分钟快手妆容｜忙碌早晨的救星',
            'cover': 'https://picsum.photos/id/72/400/300',
            'description': '专为忙碌的职场新人设计的5分钟快手妆容，简单快速又有精神。',
            'content': '职场新人们，早上时间紧张？这个5分钟快手妆容拯救你！',
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
        },
        {
            'id': '8',
            'title': '平价好物测评｜职场新人必备清单',
            'cover': 'https://picsum.photos/id/73/400/300',
            'description': '为职场新人推荐的平价好物清单，预算有限也能美美哒！',
            'content': '职场新人预算有限？这些平价好物帮你搞定职场妆容！',
            'category': 'review',
            'status': 'reviewing',
            'created_at': '2024-03-19 13:40',
            'platform': 'douyin',
            'account_id': '3',
            'stats': {
                'views': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'favorites': 0
            },
            'tags': ['平价', '好物', '测评', '职场新人']
        }
    ]
    
    for content_data in contents_data:
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
    
    db.commit()
    print(f"已导入 {len(contents_data)} 个内容")

def import_competitors(db: Session):
    """导入竞品数据"""
    print("正在导入竞品数据...")
    
    competitors_data = [
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
            'analysis_document': '''# 账号深度分析：水北山南（小红书）

## 一、账号基础画像：文艺青年的治愈系账号

### 视觉呈现：
头像采用静物元素（如书籍、咖啡杯等），避免真人出镜，营造"神秘感"与"距离感"，符合其内敛的人格标签。
采用模糊化风景 / 抽象元素（非人物肖像），强化 "文字优先" 的内容导向，避免用户因外貌标签分散注意力，契合 "重内在表达" 的人设。

### 潜在简介推断：
虽未直接展示简介，但通过内容可归纳核心标签："INFJ | 文字疗愈者 | 25 + 女性成长记录 | 生活美学探索"，强调高敏感人格的自我剖析与生活哲思。

### 主页视觉：
笔记以 "图文混排 + 文艺字体" 为主，封面统一采用低饱和色调（莫兰迪色系），如浅灰、米白、藏蓝，营造 "安静、治愈" 的浏览氛围，强化品牌视觉记忆点。

## 二、账号定位：三维度构建立体人设

### 人格标签：INFJ 的深度解构

#### 内容锚点：
80% 以上笔记携带 "#infj" 标签，通过 "高敏感特质"（如失眠、内省）、"理想主义困境"（如与现实的冲突）、"精神世界丰富性"（如对文字 / 艺术的热爱）构建人格画像。

**案例：** 笔记《一个 infj，写于她的 25 岁末尾》中，用 "烛光晃动的生日许愿" 对比 "一周后的人生变故"，展现 INFJ 型人格 "感性与理性交织" 的矛盾感。

#### 受众连接：
吸引同类人格用户（MBTI 社群）寻求认同感，同时让非 INFJ 用户产生 "探秘高敏感内心" 的好奇心。

### 年龄与身份：25-26 岁女性的 "黄金时代" 叙事

#### 阶段痛点：
- **职场：** "工作起步但无固定资产"（笔记《26 岁，在我一生的 "黄金时代"》），折射 "职场新人向轻中产过渡" 的迷茫；
- **情感：** "结束三年恋爱恢复单身"（年终总结笔记），探讨 "年龄焦虑 vs 自我价值优先" 的抉择；
- **社会角色：** "小镇做题家考上名校后的落差"（《考上名校是小镇做题家的梦醒时刻》），直击 "优绩主义崩塌" 的群体心理。

#### 身份认同：
强调 "稳定主业 + 写作副业" 的平衡模式，塑造 "理性务实又不失理想主义" 的都市女性形象，成为 25 + 女性 "想成为的样子"。

### 价值观输出：对抗焦虑的三大内核

#### 勇气哲学：
"重新出发" 贯穿多篇笔记（如年终总结、分手感悟），传递 "改变需要勇气，但更需要自我接纳" 的理念；

#### 活在当下：
反对过度规划，如《青春是一阵轻盈的晕眩》中 "浪费时间也是一种幸福"，契合 "反内卷" 的年轻群体心态；

#### 平凡美学：
拆解 "名校光环""年龄焦虑"，如《考上名校是小镇做题家的梦醒时刻》中 "承认自己是普通人"，呼吁接纳平凡的力量。

## 三、内容分析结果

### 爆款内容特征
1. **情感共鸣类**：《一个人住，越住越快乐》- 1.2w赞
2. **人生感悟类**：《26岁，在我一生的黄金时代》- 0.8w赞
3. **MBTI相关**：《infj的内心独白》- 1.5w赞

### 用户画像分析
- **年龄分布**：22-30岁（68%）
- **性别比例**：女性85%，男性15%
- **地域分布**：一二线城市占72%
- **兴趣标签**：文艺、心理学、成长、独居

### 变现能力评估
- **带货能力**：中等（主要推广书籍、文具）
- **广告合作**：较少，保持内容纯粹性
- **知识付费**：有潜力，可开设写作课程

### 内容策略建议
1. 保持真实性，避免过度包装
2. 增加互动性内容，如Q&A
3. 可考虑开设付费专栏'''
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
            'analysis_document': '''# 账号深度分析：美妆情报局（小红书）

## 一、账号基础信息

### 账号概况
- **账号名称**：美妆情报局
- **粉丝数量**：328.5w
- **内容类型**：美妆测评、产品种草
- **账号等级**：头部KOL
- **主要平台**：小红书

### 定位分析
美妆情报局定位为"专业美妆测评机构"，以客观、专业的测评内容为核心，为用户提供可信赖的美妆产品购买指南。

## 二、内容策略分析

### 内容结构
1. **新品红黑榜系列**（40%）：每周固定更新，对新上市产品进行快速测评
2. **深度测评**（30%）：单品或品类的详细对比分析
3. **成分科普**（20%）：护肤品成分解析，提升用户认知
4. **好物合集**（10%）：季节性或主题性产品推荐

### 内容特点
- **专业性强**：具备化妆品相关专业背景，测评有理有据
- **更新规律**：每周三、六固定更新，培养用户期待感
- **视觉统一**：封面采用"对比图+红色大字报"风格，识别度高
- **互动性好**：评论区积极回复，形成良好互动氛围

## 三、内容分析结果

### 爆款内容特征
1. **测评对比类**：《平价vs大牌散粉横评》- 2.3w赞
2. **新品首测**：《香奈儿新款口红试色》- 1.8w赞
3. **踩雷预警**：《这些网红产品别买》- 2.1w赞

### 用户画像分析
- **年龄分布**：18-28岁（75%）
- **性别比例**：女性95%，男性5%
- **消费能力**：中高端（月美妆消费500-2000元）
- **兴趣标签**：美妆、护肤、时尚、种草

### 变现能力评估
- **带货能力**：极强（月均GMV 200w+）
- **广告合作**：频繁，与多个品牌长期合作
- **影响力**：行业KOL，新品测评影响购买决策

### 内容策略建议
1. 保持客观性，建立信任度
2. 增加平价产品测评，扩大受众
3. 开设直播带货，提升转化率'''
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
            'analysis_document': '''# 账号深度分析：化妆师Lily（小红书）

## 一、账号基础信息

### 账号概况
- **账号名称**：化妆师Lily
- **粉丝数量**：215.3w
- **内容类型**：化妆教程、技巧分享
- **账号等级**：腰部KOL
- **职业背景**：专业化妆师

### 人设定位
化妆师Lily定位为"专业而亲和的化妆导师"，以新手友好的教学方式和专业的化妆技巧著称，是化妆新手的首选学习账号。

## 二、内容策略分析

### 内容矩阵
1. **基础教程**（50%）：针对新手的化妆基础教学
2. **进阶技巧**（30%）：化妆技巧提升和特殊场合妆容
3. **产品推荐**（15%）：适合新手的平价好物推荐
4. **答疑互动**（5%）：粉丝问题解答和直播

### 教学特色
- **循序渐进**：从最基础的化妆步骤开始教学
- **新手友好**：用语简单易懂，避免专业术语
- **实用性强**：注重日常实用的妆容教学
- **亲和力强**：语言温和，鼓励式教学

## 三、内容分析结果

### 爆款内容特征
1. **新手教程**：《5分钟学会日常妆》- 1.5w赞
2. **技巧分享**：《化妆师的10个小秘密》- 1.2w赞
3. **产品推荐**：《学生党必买的平价好物》- 0.9w赞

### 用户画像分析
- **年龄分布**：16-25岁（80%）
- **性别比例**：女性98%，男性2%
- **消费能力**：中低端（月美妆消费100-500元）
- **兴趣标签**：化妆教程、平价好物、学生党

### 变现能力评估
- **教学服务**：线上化妆课程，月收入稳定
- **带货能力**：中等，主推平价产品
- **品牌合作**：与平价品牌合作较多

### 内容策略建议
1. 制作系列化教程，建立学习体系
2. 增加进阶教程，延长用户生命周期
3. 开发线下课程，提升客单价'''
        }
    ]
    
    for competitor_data in competitors_data:
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
    
    db.commit()
    print(f"已导入 {len(competitors_data)} 个竞品")

def import_competitor_notes(db: Session):
    """导入竞品笔记数据"""
    print("正在导入竞品笔记数据...")
    
    competitor_notes_data = [
        # 水北山南的笔记
        {
            'id': '1',
            'competitor_id': '1',
            'note_id': 'note_001',
            'title': '2024年终回顾｜INFJ重新出发',
            'content_preview': '26岁，在我一生的黄金时代里，我学会了和自己和解。这一年分手了，工作变动了，搬家了，但我变得更快乐了...',
            'upload_time': '2024-03-15 19:30:00',
            'likes': 15623,
            'collects': 3241,
            'comments': 892,
            'shares': 156,
            'views': 89432,
            'engagement_rate': 17.5,
            'is_viral': True,
            'viral_score': 92,
            'content_type': '图文',
            'topics': ['INFJ', '年终总结', '成长', '自我和解'],
            'performance_rank': 1,
            'analysis': '''# 爆款笔记分析

## 标题策略
- 使用"2024年终回顾"时间锚点，触发用户回顾情绪
- "INFJ重新出发"人格标签+成长关键词，精准定位目标受众
- 符合年末总结期用户搜索习惯

## 内容结构
1. **情感铺垫**：26岁年龄标签+黄金时代概念
2. **冲突展示**：分手、工作变动、搬家等人生变故
3. **价值输出**：和解、重新出发的正向情绪
4. **共鸣触点**：INFJ人格特质的深度剖析

## 爆款要素
- 真实性：分享真实人生经历，避免鸡汤化
- 共鸣性：26岁群体的普遍焦虑与成长
- 话题性：INFJ标签带来的标签化传播
- 情绪价值：提供情感出口和认同感'''
        },
        {
            'id': '2',
            'competitor_id': '1',
            'note_id': 'note_002',
            'title': '一个人住，越住越快乐的秘密',
            'content_preview': '独居第二年，我终于找到了一个人生活的节奏。今天分享5个让独居生活更快乐的小习惯...',
            'upload_time': '2024-03-10 20:15:00',
            'likes': 12847,
            'collects': 2891,
            'comments': 674,
            'shares': 134,
            'views': 76543,
            'engagement_rate': 16.2,
            'is_viral': True,
            'viral_score': 88,
            'content_type': '图文',
            'topics': ['独居', '生活方式', '快乐', '习惯'],
            'performance_rank': 2,
            'analysis': '''# 爆款笔记分析

## 痛点击中
- 独居焦虑：社会对独居女性的偏见和担忧
- 生活质量：如何在独居中获得幸福感
- 实用价值：具体的生活技巧和建议

## 内容价值
1. 情感共鸣：独居女性的心理状态
2. 实用技巧：具体可操作的生活建议
3. 正向引导：从焦虑到快乐的转变

## 传播亮点
- 反向思维：独居=快乐，打破传统观念
- 经验分享：第二年的时间积累感
- 干货价值：5个具体习惯的实用性'''
        },
        {
            'id': '3',
            'competitor_id': '1',
            'note_id': 'note_003',
            'title': '考上名校是小镇做题家的梦醒时刻',
            'content_preview': '从小镇到北京，从名校到职场，我终于明白：优秀不是人生的全部，平凡也是一种勇气...',
            'upload_time': '2024-02-28 21:00:00',
            'likes': 9876,
            'collects': 2156,
            'comments': 543,
            'shares': 89,
            'views': 65432,
            'engagement_rate': 15.1,
            'is_viral': False,
            'viral_score': 75,
            'content_type': '图文',
            'topics': ['小镇做题家', '名校', '人生感悟', '平凡'],
            'performance_rank': 3,
            'analysis': '''# 深度内容分析

## 话题热度
- "小镇做题家"社会热议话题
- 教育公平和阶层跃迁讨论
- 名校光环与现实落差的反思

## 情感层次
1. 身份认同：小镇青年的标签化
2. 心理变化：从优越感到平常心
3. 价值重塑：重新定义成功

## 受众价值
- 同类人群的心理慰藉
- 社会议题的深度思考
- 成长心态的积极引导'''
        },
        
        # 美妆情报局的笔记
        {
            'id': '4',
            'competitor_id': '2',
            'note_id': 'note_004',
            'title': '3月新品红黑榜｜这些别买！',
            'content_preview': '测了整整一个月的新品，终于可以跟大家分享3月的红黑榜了！有些产品真的让我失望...',
            'upload_time': '2024-03-18 18:00:00',
            'likes': 23456,
            'collects': 5678,
            'comments': 1234,
            'shares': 345,
            'views': 156789,
            'engagement_rate': 19.8,
            'is_viral': True,
            'viral_score': 95,
            'content_type': '图文',
            'topics': ['新品测评', '红黑榜', '避雷', '美妆'],
            'performance_rank': 1,
            'analysis': '''# 测评类爆款分析

## 标题策略
- 时效性："3月新品"明确时间
- 争议性："红黑榜"+"别买"引发好奇
- 权威性：暗示专业测评结果

## 内容价值
1. 专业测评：一个月深度体验
2. 避雷指南：帮助用户避免踩坑
3. 购买决策：提供具体选择建议

## 互动设计
- 争议话题引发讨论
- 评论区答疑提升粘性
- 分享价值促进传播'''
        },
        {
            'id': '5',
            'competitor_id': '2',
            'note_id': 'note_005',
            'title': '平价替代合集｜大牌平替真的好用吗？',
            'content_preview': '花了2000块买了10个大牌和它们的平价替代，逐一对比告诉你哪些真的值得买...',
            'upload_time': '2024-03-12 19:30:00',
            'likes': 18765,
            'collects': 4321,
            'comments': 987,
            'shares': 234,
            'views': 123456,
            'engagement_rate': 18.2,
            'is_viral': True,
            'viral_score': 89,
            'content_type': '图文',
            'topics': ['平价替代', '大牌平替', '性价比', '对比测评'],
            'performance_rank': 2,
            'analysis': '''# 对比测评成功要素

## 用户痛点
- 预算限制：想要大牌效果但价格敏感
- 选择困难：平替产品众多，难以筛选
- 效果疑虑：平替是否真的有效

## 内容优势
1. 客观对比：大牌vs平替直观展示
2. 投入成本：2000元投入体现专业度
3. 结论明确：给出具体购买建议

## 商业价值
- 带货能力强：平替产品价格亲民
- 复购率高：建立用户信任度
- 品牌合作：平替品牌合作机会'''
        },
        
        # 化妆师Lily的笔记  
        {
            'id': '6',
            'competitor_id': '3',
            'note_id': 'note_006',
            'title': '新手必看！5分钟学会日常妆容',
            'content_preview': '很多姐妹说化妆太难，今天教大家一个超简单的日常妆容，新手5分钟就能学会...',
            'upload_time': '2024-03-14 17:00:00',
            'likes': 15234,
            'collects': 3456,
            'comments': 789,
            'shares': 178,
            'views': 98765,
            'engagement_rate': 17.8,
            'is_viral': True,
            'viral_score': 85,
            'content_type': '图文+视频',
            'topics': ['新手教程', '日常妆容', '化妆教学', '简单'],
            'performance_rank': 1,
            'analysis': '''# 教程类内容分析

## 目标受众
- 化妆新手：技能零基础用户
- 时间紧张：上班族快速妆容需求
- 预算有限：使用平价产品教学

## 教学特色
1. 时间明确：5分钟时长降低学习门槛
2. 步骤简化：删繁就简突出重点
3. 新手友好：避免复杂技巧和产品

## 价值输出
- 技能传授：具体操作步骤
- 信心建立：简单易学增强自信
- 习惯养成：日常妆容规律化'''
        },
        {
            'id': '7',
            'competitor_id': '3',
            'note_id': 'note_007',
            'title': '化妆师私藏技巧｜这样画眉毛不会错',
            'content_preview': '做了5年化妆师，今天分享我的画眉秘籍，掌握这3个要点，新手也能画出完美眉形...',
            'upload_time': '2024-03-08 16:30:00',
            'likes': 12678,
            'collects': 2890,
            'comments': 567,
            'shares': 145,
            'views': 87654,
            'engagement_rate': 16.5,
            'is_viral': False,
            'viral_score': 78,
            'content_type': '图文',
            'topics': ['眉毛', '化妆技巧', '化妆师', '教程'],
            'performance_rank': 2,
            'analysis': '''# 专业技巧分享分析

## 权威性建立
- 职业背景：5年化妆师经验
- 专业技巧：私藏秘籍的独特性
- 成果承诺：完美眉形的效果保证

## 内容结构
1. 问题识别：新手画眉难点
2. 方法传授：3个关键要点
3. 效果展示：完美眉形案例

## 学习价值
- 专业度：化妆师级别的技巧
- 实用性：日常可操作的方法
- 普适性：适合不同脸型眉形'''
        },
        {
            'id': '8',
            'competitor_id': '3',
            'note_id': 'note_008',
            'title': '学生党福利｜20元搞定全套底妆',
            'content_preview': '预算有限的学生党看过来！今天用不到20元的产品，教大家打造完整底妆，效果不输大牌...',
            'upload_time': '2024-03-05 19:00:00',
            'likes': 11234,
            'collects': 2567,
            'comments': 456,
            'shares': 123,
            'views': 76543,
            'engagement_rate': 15.9,
            'is_viral': False,
            'viral_score': 72,
            'content_type': '图文',
            'topics': ['学生党', '平价', '底妆', '预算'],
            'performance_rank': 3,
            'analysis': '''# 平价教程内容分析

## 受众定位
- 学生群体：预算限制明显
- 新手用户：对产品选择困难
- 性价比追求者：效果与价格平衡

## 内容卖点
1. 价格优势：20元超低预算
2. 效果保证：不输大牌的承诺
3. 教学完整：全套底妆流程

## 社会价值
- 降低美妆门槛：让更多人享受美妆乐趣
- 理性消费：倡导根据预算合理选择
- 技巧分享：专业知识的普及'''
        }
    ]
    
    for note_data in competitor_notes_data:
        note = CompetitorNote(**note_data)
        db.add(note)
    
    db.commit()
    print(f"已导入 {len(competitor_notes_data)} 条竞品笔记")

def import_tasks(db: Session):
    """导入任务数据"""
    print("正在导入任务数据...")
    
    tasks_data = [
        {
            'id': '1',
            'title': '创建油皮护肤测评内容',
            'description': '针对油皮人群创建5款平价控油产品的测评内容',
            'deadline': datetime(2024, 3, 20),
            'status': 'inProgress',
            'priority': 'high',
            'type': 'content',
            'assignee': '张运营',
            'progress': 60,
            'account_id': '1'
        },
        {
            'id': '2',
            'title': '竞品账号数据分析',
            'description': '分析3个头部美妆账号的内容数据和运营策略',
            'deadline': datetime(2024, 3, 22),
            'status': 'pending',
            'priority': 'medium',
            'type': 'analysis',
            'assignee': '李分析',
            'progress': 0
        },
        {
            'id': '3',
            'title': '制定6月内容发布计划',
            'description': '根据数据分析结果，制定6月的内容发布计划和频率',
            'deadline': datetime(2024, 3, 25),
            'status': 'pending',
            'priority': 'low',
            'type': 'schedule',
            'assignee': '王策划',
            'progress': 0
        },
        {
            'id': '4',
            'title': '粉丝互动活动策划',
            'description': '策划一次粉丝参与度高的互动活动，提高账号活跃度',
            'deadline': datetime(2024, 3, 18),
            'status': 'overdue',
            'priority': 'high',
            'type': 'operation',
            'assignee': '张运营',
            'progress': 80,
            'account_id': '1'
        },
        {
            'id': '5',
            'title': '数据周报整理',
            'description': '整理过去一周的账号数据表现，生成周报',
            'deadline': datetime(2024, 3, 15),
            'status': 'completed',
            'priority': 'medium',
            'type': 'analysis',
            'assignee': '李分析',
            'progress': 100
        },
        {
            'id': '6',
            'title': '小红书账号冷启动期执行',
            'description': '执行小红书账号冷启动期运营SOP，包括账号装修、内容储备等',
            'deadline': datetime(2024, 4, 15),
            'status': 'inProgress',
            'priority': 'high',
            'type': 'operation',
            'assignee': '运营团队',
            'progress': 30,
            'account_id': '1',
            'sop_data': {
                'phase': 'cold-start',
                'week': 1,
                'tasks': [
                    {
                        'name': '账号装修',
                        'completed': True,
                        'completion_date': '2024-03-16'
                    },
                    {
                        'name': '内容储备',
                        'completed': True,
                        'completion_date': '2024-03-18'
                    },
                    {
                        'name': '账号认证',
                        'completed': False,
                        'target_date': '2024-03-25'
                    }
                ]
            }
        },
        {
            'id': '7',
            'title': '竞品爆款内容分析',
            'description': '分析美妆情报局最新爆款内容的成功要素和可复制策略',
            'deadline': datetime(2024, 3, 30),
            'status': 'pending',
            'priority': 'medium',
            'type': 'analysis',
            'assignee': '内容策划',
            'progress': 0,
            'related_competitor': '美妆情报局',
            'analysis_focus': ['标题策略', '封面设计', '内容结构', '互动引导']
        },
        {
            'id': '8',
            'title': '知识库文档整理',
            'description': '整理化妆师教学技巧的知识库文档，形成可复用的教程模板',
            'deadline': datetime(2024, 4, 5),
            'status': 'inProgress',
            'priority': 'low',
            'type': 'content',
            'assignee': '内容团队',
            'progress': 25,
            'knowledge_type': 'tutorial_template',
            'categories': ['新手教程', '进阶技巧', '产品推荐', '答疑模板']
        }
    ]
    
    for task_data in tasks_data:
        # 提取基础字段
        basic_fields = {
            'id': task_data['id'],
            'title': task_data['title'],
            'description': task_data['description'],
            'deadline': task_data['deadline'],
            'status': task_data['status'],
            'priority': task_data['priority'],
            'type': task_data['type'],
            'assignee': task_data['assignee'],
            'progress': task_data['progress'],
            'account_id': task_data.get('account_id')
        }
        
        # 添加额外数据到描述中
        extra_info = {}
        if 'sop_data' in task_data:
            extra_info['sop_data'] = task_data['sop_data']
        if 'related_competitor' in task_data:
            extra_info['related_competitor'] = task_data['related_competitor']
        if 'analysis_focus' in task_data:
            extra_info['analysis_focus'] = task_data['analysis_focus']
        if 'knowledge_type' in task_data:
            extra_info['knowledge_type'] = task_data['knowledge_type']
        if 'categories' in task_data:
            extra_info['categories'] = task_data['categories']
            
        if extra_info:
            basic_fields['description'] += f"\n\n额外信息：{json.dumps(extra_info, ensure_ascii=False, indent=2)}"
        
        task = Task(**basic_fields)
        db.add(task)
    
    db.commit()
    print(f"已导入 {len(tasks_data)} 个任务")

def import_schedules(db: Session):
    """导入发布计划数据"""
    print("正在导入发布计划数据...")
    
    schedules_data = [
        {
            'id': str(uuid.uuid4())[:8],
            'title': '护肤小白教程发布',
            'description': '护肤步骤教程的定时发布',
            'type': 'single',
            'status': 'pending',
            'account_id': '1',
            'content_id': '4',
            'platform': 'xiaohongshu',
            'publish_datetime': datetime(2024, 3, 20, 19, 0),
            'note': '黄金时间发布，预期效果较好'
        },
        {
            'id': str(uuid.uuid4())[:8],
            'title': '轻奢美妆好物推荐',
            'description': '轻奢美妆产品的推荐内容发布',
            'type': 'single',
            'status': 'pending',
            'account_id': '2',
            'content_id': '6',
            'platform': 'xiaohongshu',
            'publish_datetime': datetime(2024, 3, 22, 18, 30),
            'note': '职场下班时间发布'
        }
    ]
    
    for schedule_data in schedules_data:
        schedule = Schedule(
            id=schedule_data['id'],
            title=schedule_data['title'],
            description=schedule_data['description'],
            type=schedule_data['type'],
            status=schedule_data['status'],
            account_id=schedule_data['account_id'],
            content_id=schedule_data['content_id'],
            platform=schedule_data['platform'],
            publish_datetime=schedule_data['publish_datetime'],
            note=schedule_data['note']
        )
        db.add(schedule)
    
    db.commit()
    print(f"已导入 {len(schedules_data)} 个发布计划")

def import_chat_messages(db: Session):
    """导入聊天消息数据"""
    print("正在导入聊天消息数据...")
    
    messages_data = [
        {
            'id': str(uuid.uuid4())[:8],
            'content': '👋 你好！我是SocialPulse AI，你的智能社交媒体运营助手。我可以帮你分析账号定位、拆解竞品、生成内容，还能管理多平台账号。',
            'sender': 'ai',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'received',
            'user_id': 'test_user',
            'session_id': 'default_session'
        }
    ]
    
    for msg_data in messages_data:
        message = ChatMessage(
            id=msg_data['id'],
            content=msg_data['content'],
            sender=msg_data['sender'],
            timestamp=msg_data['timestamp'],
            status=msg_data['status'],
            user_id=msg_data['user_id'],
            session_id=msg_data['session_id']
        )
        db.add(message)
    
    db.commit()
    print(f"已导入 {len(messages_data)} 条聊天消息")

def main():
    """主函数"""
    print("开始导入mock数据到数据库...")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 清空现有数据
        clean_database(db)
        
        # 导入各种数据
        import_accounts(db)
        import_contents(db)
        import_competitors(db)
        import_competitor_notes(db)
        import_tasks(db)
        import_schedules(db)
        import_chat_messages(db)
        
        print("\n🎉 所有mock数据导入成功！")
        print("可以通过API测试页面验证数据是否正确导入。")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 