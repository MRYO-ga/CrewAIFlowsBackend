from typing import List, Dict, Any, Optional, Type
from datetime import datetime, timedelta
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import random
import json
import os

# 输入参数模型定义
class XiaoHongShuSearchInput(BaseModel):
    """小红书搜索输入参数"""
    query: str = Field(..., description="搜索关键词")
    num: int = Field(default=10, description="需要返回的结果数量")
    note_type: int = Field(default=0, description="笔记类型，0:全部, 1:视频, 2:图文")

class XiaoHongShuPublishInput(BaseModel):
    """小红书发布输入参数"""
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记内容")
    images: List[str] = Field(default=[], description="图片URL列表")
    tags: List[str] = Field(default=[], description="标签列表")

class XiaoHongShuAccountInput(BaseModel):
    """小红书账号输入参数"""
    account_id: str = Field(..., description="账号ID")

class XiaoHongShuComplianceInput(BaseModel):
    """小红书合规检查输入参数"""
    content: str = Field(..., description="待检查的内容")

# 获取用户信息工具输入模型
class UserInfoInput(BaseModel):
    """获取用户信息工具的输入参数"""
    account_id: str = Field(..., description="小红书账号ID")

# 获取关键词联想词工具输入模型
class SearchKeywordInput(BaseModel):
    """获取关键词联想词工具的输入参数"""
    keyword: str = Field(..., description="核心关键词")

# 搜索用户工具输入模型
class SearchUserInput(BaseModel):
    """搜索用户工具的输入参数"""
    keyword: str = Field(..., description="搜索关键词")
    limit: int = Field(default=20, description="返回结果限制数量")

# 获取用户所有笔记工具输入模型
class UserAllNotesInput(BaseModel):
    """获取用户所有笔记工具的输入参数"""
    user_id: str = Field(..., description="用户ID")
    limit: int = Field(default=50, description="返回结果限制数量")

# 获取首页推荐内容工具输入模型
class HomefeedRecommendInput(BaseModel):
    """获取首页推荐内容工具的输入参数"""
    category: str = Field(..., description="内容品类，如'护肤'、'健身'等")
    num: int = Field(default=50, description="返回结果数量")

# 搜索笔记工具输入模型
class SearchNoteInput(BaseModel):
    """搜索笔记工具的输入参数"""
    keyword: str = Field(..., description="搜索关键词")
    days: int = Field(default=30, description="限定天数范围")
    min_likes: int = Field(default=0, description="最小点赞数")
    sort_by: str = Field(default="hot", description="排序方式，hot或time")

# 获取笔记详情工具输入模型
class NoteInfoInput(BaseModel):
    """获取笔记详情工具的输入参数"""
    note_id: str = Field(..., description="笔记ID")

# 获取无水印视频工具输入模型
class NoWaterVideoInput(BaseModel):
    """获取无水印视频工具的输入参数"""
    note_id: str = Field(..., description="笔记ID")

class XiaoHongShuContentTool(BaseTool):
    """小红书内容工具"""
    name: str = "xiaohongshu_content_tool"
    description: str = "用于搜索、分析和生成小红书内容的工具。可以搜索笔记、分析内容特点等。"
    args_schema: Type[BaseModel] = XiaoHongShuSearchInput

    def _run(self, query: str, num: int = 10, note_type: int = 0) -> Dict[str, Any]:
        """执行小红书内容搜索"""
        # 实际实现中调用小红书API
        return {
            "success": True,
            "results": [
                {
                    "title": f"搜索结果{i+1}",
                    "content": f"内容{i+1}",
                    "likes": 100 * (i+1)
                } for i in range(num)
            ]
        }

    async def _arun(self, query: str, num: int = 10, note_type: int = 0) -> Dict[str, Any]:
        """异步执行小红书内容搜索"""
        raise NotImplementedError("暂不支持异步操作")

class XiaoHongShuPublicationTool(BaseTool):
    """小红书发布工具"""
    name: str = "xiaohongshu_publication_tool"
    description: str = "用于发布和管理小红书内容的工具。可以发布笔记、设置定时发布、添加标签等。"
    args_schema: Type[BaseModel] = XiaoHongShuPublishInput

    def _run(self, title: str, content: str, images: List[str] = None, tags: List[str] = None) -> Dict[str, Any]:
        """发布小红书内容"""
        # 实际实现中调用小红书API
        return {
            "success": True,
            "publication_id": "pub_123456",
            "url": "https://xiaohongshu.com/note/123456"
        }

    async def _arun(self, title: str, content: str, images: List[str] = None, tags: List[str] = None) -> Dict[str, Any]:
        """异步发布小红书内容"""
        raise NotImplementedError("暂不支持异步操作")

class XiaoHongShuCompetitorTool(BaseTool):
    """小红书竞品分析工具"""
    name: str = "xiaohongshu_competitor_tool"
    description: str = "用于分析竞品账号和内容的工具。可以分析竞品账号数据、爆款内容特点等。"
    args_schema: Type[BaseModel] = XiaoHongShuAccountInput

    def _run(self, account_id: str) -> Dict[str, Any]:
        """分析竞品账号"""
        # 实际实现中调用小红书API
        return {
            "success": True,
            "account_info": {
                "followers": 10000,
                "posts": 100,
                "engagement_rate": 5.2
            }
        }

    async def _arun(self, account_id: str) -> Dict[str, Any]:
        """异步分析竞品账号"""
        raise NotImplementedError("暂不支持异步操作")

class XiaoHongShuAccountTool:
    """小红书账号工具类，提供小红书相关API接口封装"""
    
    def __init__(self):
        """初始化工具类"""
        self.api_base = "https://api.xiaohongshu.com"
        
    def fetch_account_info(self, account_id: str) -> Dict[str, Any]:
        """
        获取账号基本信息
        
        Args:
            account_id: 小红书账号ID
            
        Returns:
            Dict: 账号基本信息
        """
        # 模拟API调用
        mock_data = {
            "id": account_id,
            "name": "测试账号" if not account_id else f"小红书账号_{account_id[:5]}",
            "followers": random.randint(1000, 50000),
            "following": random.randint(100, 500),
            "notes_count": random.randint(50, 200),
            "likes_count": random.randint(5000, 100000),
            "bio": "这是一个测试账号的简介，专注于分享优质内容",
        }
        
        return mock_data
        
    def update_account_persona(self, account_id: str, data: Dict[str, Any]) -> bool:
        """
        更新账号人设信息
        
        Args:
            account_id: 小红书账号ID
            data: 要更新的数据
            
        Returns:
            bool: 更新是否成功
        """
        # 模拟API调用
        success = True
        print(f"更新账号 {account_id} 信息: {json.dumps(data, ensure_ascii=False)}")
        return success
    
    def get_user_info(self, account_id: str) -> Dict[str, Any]:
        """
        分析对标账号的名称/简介结构
        
        Args:
            account_id: 小红书账号ID
            
        Returns:
            Dict: 账号详细信息分析
        """
        # 模拟API返回热门账号的名称结构和简介特点分析
        account_types = [
            "专业型", "生活方式型", "知识分享型", "个性化IP型", "兴趣爱好型"
        ]
        
        name_structures = [
            "领域+身份标识（如：护肤小谯言）",
            "人物特征+专业领域（如：办公室健身小C）",
            "创意昵称+emoji（如：肌肤守护者🛡️）",
            "故事化昵称（如：深夜健身房）",
            "专业度+领域（如：认证香水师）"
        ]
        
        bio_features = [
            "数据化承诺（8年经验|100+产品测评）",
            "专业身份认证（XX大学|XX证书持有者）",
            "内容预期（每周X更新|干货分享）",
            "个性化标语（拒绝虚假种草|只分享真实体验）",
            "互动引导（关注我了解更多|评论区告诉我你想看什么）"
        ]
        
        account_type = random.choice(account_types)
        selected_name_structures = random.sample(name_structures, 2)
        selected_bio_features = random.sample(bio_features, 3)
        
        return {
            "account_id": account_id,
            "account_type": account_type,
            "name_structure_analysis": selected_name_structures,
            "bio_features": selected_bio_features,
            "recommendation": f"建议采用{account_type}定位，使用{selected_name_structures[0]}命名结构，简介中加入{selected_bio_features[0]}元素提升专业感"
        }
    
    def get_search_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        获取搜索关键词的联想词
        
        Args:
            keyword: 核心关键词
            
        Returns:
            Dict: 关键词相关联想词和分析
        """
        # 模拟API返回关键词联想分析
        keyword_categories = {
            "护肤": ["敏感肌护肤", "油皮护肤", "抗老护肤", "美白护肤", "保湿补水"],
            "健身": ["居家健身", "办公室健身", "增肌健身", "减脂健身", "通勤健身"],
            "美食": ["家常菜谱", "减脂餐", "下午茶", "早餐食谱", "快手料理"],
            "穿搭": ["日常穿搭", "职场穿搭", "约会穿搭", "轻奢穿搭", "显瘦穿搭"]
        }
        
        # 决定使用哪个类别的关键词
        category = None
        for cat, keywords in keyword_categories.items():
            if keyword.lower() in cat.lower():
                category = cat
                break
        
        # 如果找不到匹配的类别，使用默认类别
        if not category:
            category = random.choice(list(keyword_categories.keys()))
        
        # 获取相关联想词
        related_keywords = keyword_categories[category]
        search_volume = [random.randint(1000, 50000) for _ in range(len(related_keywords))]
        
        # 创建排序后的关键词和搜索量的列表
        keyword_data = list(zip(related_keywords, search_volume))
        keyword_data.sort(key=lambda x: x[1], reverse=True)
        
        top_keywords = [k for k, _ in keyword_data[:3]]
        
        return {
            "core_keyword": keyword,
            "related_keywords": related_keywords,
            "search_volume": dict(zip(related_keywords, search_volume)),
            "top_recommendations": top_keywords,
            "analysis": f"搜索'{keyword}'的用户多关注'{top_keywords[0]}'和'{top_keywords[1]}'相关内容，建议在账号标签和内容中加入这些关键词以提高曝光"
        }
    
    def search_user(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        """
        搜索同领域账号
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果限制
            
        Returns:
            Dict: 账号列表和分析
        """
        # 模拟API返回搜索结果
        results = []
        persona_keywords = [
            "专业", "达人", "博主", "教练", "老师", "测评师", "种草官", "创作者", 
            "生活家", "设计师", "玩家", "健身达人", "搭配师", "美妆博主"
        ]
        
        for i in range(limit):
            persona_type = random.choice(persona_keywords)
            follower_count = random.randint(1000, 500000)
            
            results.append({
                "user_id": f"user_{i}_{keyword.replace(' ', '_')}",
                "nickname": f"{keyword}{persona_type}{i+1}号",
                "follower_count": follower_count,
                "notes_count": random.randint(50, 300),
                "persona_keywords": random.sample(persona_keywords, 3),
                "description": f"专注于{keyword}内容分享" if i % 3 != 0 else f"{keyword}领域创作者，提供专业{keyword}指导"
            })
        
        # 按粉丝数排序
        results.sort(key=lambda x: x["follower_count"], reverse=True)
        
        # 分析人设同质化问题
        common_keywords = set()
        for result in results[:5]:  # 只分析前5个账号
            common_keywords.update(result["persona_keywords"])
        
        return {
            "accounts": results,
            "analysis": {
                "total_found": len(results),
                "common_persona_keywords": list(common_keywords),
                "homogenization_issues": f"在{keyword}领域前20名账号中，{round(len(results) * 0.7)}个使用类似人设定位，建议避免使用{list(common_keywords)[:3]}等高频人设关键词，寻找差异化定位"
            }
        }
    
    def get_user_all_notes(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        获取用户所有笔记
        
        Args:
            user_id: 用户ID
            limit: 返回结果限制
            
        Returns:
            Dict: 包含笔记列表和分析
        """
        # 模拟笔记主题
        topics = ["产品测评", "使用教程", "经验分享", "问题解决", "新品推荐", "科普知识", "趋势分析"]
        
        # 模拟笔记格式
        formats = ["图文测评", "视频记录", "清单总结", "问答解析", "步骤教程", "对比分析"]
        
        # 生成随机笔记数据
        notes = []
        for i in range(limit):
            topic = random.choice(topics)
            note_format = random.choice(formats)
            
            notes.append({
                "note_id": f"note_{i}_{user_id}",
                "title": f"{topic}：{note_format}{i+1}",
                "type": "图文" if random.random() > 0.3 else "视频",
                "likes": random.randint(10, 5000),
                "comments": random.randint(0, 200),
                "collects": random.randint(5, 500),
                "create_time": f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}",
                "topic": topic,
                "format": note_format
            })
        
        # 分析主题分布
        topic_distribution = {}
        for note in notes:
            topic = note["topic"]
            topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
        
        # 转换为百分比
        for topic in topic_distribution:
            topic_distribution[topic] = round(topic_distribution[topic] / len(notes) * 100)
        
        # 分析高频人设关键词
        format_distribution = {}
        for note in notes:
            format_name = note["format"]
            format_distribution[format_name] = format_distribution.get(format_name, 0) + 1
        
        return {
            "user_id": user_id,
            "notes_count": len(notes),
            "notes": notes,
            "analysis": {
                "topic_distribution": topic_distribution,
                "format_distribution": format_distribution,
                "top_performing_topics": [k for k, v in sorted(topic_distribution.items(), key=lambda item: item[1], reverse=True)][:3],
                "persona_keywords": ["专业", "实用", "深度" if random.random() > 0.5 else "通俗易懂"],
                "content_focus": f"内容{round(topic_distribution.get('产品测评', 0) + topic_distribution.get('经验分享', 0))}%集中在产品测评和经验分享，建议开拓更多{random.choice(list(set(topics) - {'产品测评', '经验分享'}))}类内容"
            }
        }
    
    def get_homefeed_recommend_by_num(self, category: str, num: int = 50) -> Dict[str, Any]:
        """
        获取首页推荐内容
        
        Args:
            category: 内容品类
            num: 返回结果数量
            
        Returns:
            Dict: 推荐内容列表和分析
        """
        # 内容形式列表
        content_forms = [
            "问题-解决方案图文", "步骤分解图文", "对比图文", "清单型图文", 
            "跟练视频", "Vlog视频", "测评视频", "知识点讲解视频"
        ]
        
        # 生成随机推荐内容
        recommendations = []
        for i in range(num):
            content_form = random.choice(content_forms)
            is_video = "视频" in content_form
            
            recommendations.append({
                "note_id": f"note_{i}_{category.replace(' ', '_')}",
                "title": f"{random.choice(['如何', '为什么', '这样做', '必看'])}：{category}{content_form}内容{i+1}",
                "type": "视频" if is_video else "图文",
                "likes": random.randint(500, 50000),
                "comments": random.randint(10, 2000),
                "collects": random.randint(100, 10000),
                "create_time": f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}",
                "content_form": content_form,
                "has_purchase": random.choice([True, False, False, False])  # 25%概率有购物链接
            })
        
        # 按互动量排序
        recommendations.sort(key=lambda x: x["likes"] + x["comments"]*3 + x["collects"]*2, reverse=True)
        
        # 分析内容形式分布
        form_distribution = {}
        for rec in recommendations:
            form = rec["content_form"]
            form_distribution[form] = form_distribution.get(form, 0) + 1
        
        # 转换为百分比
        for form in form_distribution:
            form_distribution[form] = round(form_distribution[form] / len(recommendations) * 100)
        
        # 分析视频与图文比例
        video_count = sum(1 for rec in recommendations if rec["type"] == "视频")
        video_percentage = round(video_count / len(recommendations) * 100)
        
        # 分析标题特征
        title_features = []
        if any("如何" in rec["title"] for rec in recommendations[:10]):
            title_features.append("问题解决型")
        if any("必看" in rec["title"] for rec in recommendations[:10]):
            title_features.append("强调重要性")
        if any(str(n) in rec["title"] for n in range(1, 10) for rec in recommendations[:10]):
            title_features.append("数字引导型")
        
        return {
            "category": category,
            "total_recommendations": len(recommendations),
            "top_recommendations": recommendations[:10],
            "analysis": {
                "content_form_distribution": form_distribution,
                "video_percentage": video_percentage,
                "image_text_percentage": 100 - video_percentage,
                "title_features": title_features,
                "trending_forms": [k for k, v in sorted(form_distribution.items(), key=lambda item: item[1], reverse=True)][:3],
                "insight": f"在{category}品类中，{[k for k, v in sorted(form_distribution.items(), key=lambda item: item[1], reverse=True)][0]}最受欢迎，占比{form_distribution[[k for k, v in sorted(form_distribution.items(), key=lambda item: item[1], reverse=True)][0]]}%，建议优先采用此内容形式"
            }
        }
    
    def search_note(self, keyword: str, days: int = 30, min_likes: int = 0, sort_by: str = "hot") -> Dict[str, Any]:
        """
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            days: 限定天数范围
            min_likes: 最小点赞数
            sort_by: 排序方式，hot或time
            
        Returns:
            Dict: 笔记列表和分析
        """
        # 生成随机搜索结果
        num_results = random.randint(30, 100)
        results = []
        
        # 常见标题结构
        title_structures = [
            "数字+痛点+解决方案",
            "疑问句+答案暗示",
            "强调词+核心利益点",
            "紧急感+关键结果",
            "对比型+转折"
        ]
        
        # 内容类型
        content_types = ["教程", "分享", "测评", "记录", "总结", "攻略"]
        
        # 生成搜索结果
        for i in range(num_results):
            likes = random.randint(10, 20000)
            if likes < min_likes:
                likes = min_likes + random.randint(0, 1000)
                
            content_type = random.choice(content_types)
            title_structure = random.choice(title_structures)
            
            # 根据标题结构生成标题
            if "数字" in title_structure:
                title = f"{random.randint(1, 10)}个{keyword}{content_type}方法"
            elif "疑问句" in title_structure:
                title = f"如何掌握{keyword}的{content_type}技巧？"
            elif "强调词" in title_structure:
                title = f"必学！{keyword}{content_type}绝技"
            elif "紧急感" in title_structure:
                title = f"速收藏！{keyword}高效{content_type}"
            else:
                title = f"以前vs现在：{keyword}{content_type}新方法"
            
            results.append({
                "note_id": f"note_search_{i}",
                "title": title,
                "type": "视频" if random.random() > 0.6 else "图文",
                "likes": likes,
                "comments": random.randint(5, min(likes//2, 1000)),
                "collects": random.randint(10, min(likes//1.5, 2000)),
                "create_time": f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}",
                "content_type": content_type,
                "title_structure": title_structure
            })
        
        # 按点赞数排序
        if sort_by == "hot":
            results.sort(key=lambda x: x["likes"], reverse=True)
        else:
            # 按时间排序，这里简单模拟
            random.shuffle(results)
        
        # 筛选满足点赞要求的笔记
        filtered_results = [r for r in results if r["likes"] >= min_likes]
        
        # 分析高频选题
        topic_count = {}
        for result in filtered_results:
            topic = result["content_type"]
            topic_count[topic] = topic_count.get(topic, 0) + 1
        
        # 分析标题结构
        structure_count = {}
        for result in filtered_results:
            structure = result["title_structure"]
            structure_count[structure] = structure_count.get(structure, 0) + 1
        
        return {
            "keyword": keyword,
            "days_range": days,
            "min_likes": min_likes,
            "total_results": len(filtered_results),
            "notes": filtered_results[:20],  # 只返回前20条结果
            "analysis": {
                "popular_topics": {k: round(v/len(filtered_results)*100) for k, v in sorted(topic_count.items(), key=lambda item: item[1], reverse=True)},
                "effective_title_structures": {k: round(v/len(filtered_results)*100) for k, v in sorted(structure_count.items(), key=lambda item: item[1], reverse=True)},
                "high_engagement_topics": [k for k, v in sorted(topic_count.items(), key=lambda item: item[1], reverse=True)][:3],
                "recommendation": f"建议优先创作{[k for k, v in sorted(topic_count.items(), key=lambda item: item[1], reverse=True)][0]}类型内容，使用{[k for k, v in sorted(structure_count.items(), key=lambda item: item[1], reverse=True)][0]}标题结构，可显著提高内容曝光度"
            }
        }
        
    def get_note_info(self, note_id: str) -> Dict[str, Any]:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
            
        Returns:
            Dict: 笔记详情
        """
        # 模拟笔记详情
        note_type = "视频" if random.random() > 0.6 else "图文"
        likes = random.randint(500, 50000)
        
        # 标题结构类型
        title_structures = {
            "数字引导型": f"{random.randint(1, 10)}个小技巧让你轻松掌握",
            "问题解决型": "如何解决长久困扰的问题？",
            "利益暗示型": "学会这个技巧，效率提升300%",
            "紧急感型": "必看！这些错误你一定在犯",
            "对比转折型": "对比：从入门到精通的蜕变"
        }
        
        structure_type = random.choice(list(title_structures.keys()))
        title = title_structures[structure_type]
        
        # 内容结构
        content_structure = {
            "引言": "点明痛点，引发共鸣",
            "主体": "分步骤/分点展示核心内容",
            "结尾": "总结要点，引导互动/关注"
        }
        
        # 互动数据
        interaction_data = {
            "likes": likes,
            "comments": random.randint(10, min(likes//3, 2000)),
            "collects": random.randint(50, min(likes//2, 5000)),
            "shares": random.randint(5, min(likes//4, 1000))
        }
        
        # 用户评论关键词
        comment_keywords = ["实用", "干货", "学到了", "感谢分享", "收藏了"]
        
        return {
            "note_id": note_id,
            "title": title,
            "title_structure": structure_type,
            "type": note_type,
            "content_structure": content_structure,
            "interaction_data": interaction_data,
            "comment_keywords": random.sample(comment_keywords, 3),
            "analysis": {
                "engagement_rate": round((interaction_data["comments"] + interaction_data["shares"]) / interaction_data["likes"] * 100),
                "collection_rate": round(interaction_data["collects"] / interaction_data["likes"] * 100),
                "title_effectiveness": "高" if interaction_data["likes"] > 5000 else "中",
                "recommended_improvement": f"建议在{random.choice(['标题', '开头', '结尾'])}增加{random.choice(['用户引导', '数据支持', '情感共鸣'])}元素，提升互动率"
            }
        }
    
    def get_note_no_water_video(self, note_id: str) -> Dict[str, Any]:
        """
        获取笔记无水印视频链接
        
        Args:
            note_id: 笔记ID
            
        Returns:
            Dict: 无水印视频信息
        """
        return {
            "note_id": note_id,
            "video_url": f"https://example.com/xhs/video/{note_id}.mp4",
            "duration": random.randint(15, 180),
            "resolution": random.choice(["1080p", "720p"]),
            "message": "视频链接已生成，仅供学习参考"
        }

class XiaoHongShuComplianceTool(BaseTool):
    """小红书合规检查工具"""
    name: str = "xiaohongshu_compliance_tool"
    description: str = "用于检查内容合规性和敏感词的工具。可以检查内容是否违规、包含敏感词等。"
    args_schema: Type[BaseModel] = XiaoHongShuComplianceInput

    def _run(self, content: str) -> Dict[str, Any]:
        """检查内容合规性"""
        # 实际实现中调用合规检查API
        return {
            "success": True,
            "is_compliant": True,
            "issues": []
        }

    async def _arun(self, content: str) -> Dict[str, Any]:
        """异步检查内容合规性"""
        raise NotImplementedError("暂不支持异步操作")

# 工具类定义

class GetUserInfoTool(BaseTool):
    """分析对标账号的名称/简介结构工具"""
    name: str = "get_user_info"
    description: str = "分析对标账号的名称结构与简介特点，如分析头部账号'办公室健身小C'的名称构成"
    args_schema: Type[BaseModel] = UserInfoInput

    def _run(self, account_id: str) -> Dict[str, Any]:
        """
        分析对标账号的名称/简介结构
        
        Args:
            account_id: 小红书账号ID
            
        Returns:
            Dict: 账号详细信息分析
        """
        # 模拟API返回热门账号的名称结构和简介特点分析
        account_types = [
            "专业型", "生活方式型", "知识分享型", "个性化IP型", "兴趣爱好型"
        ]
        
        name_structures = [
            "领域+身份标识（如：护肤小谯言）",
            "人物特征+专业领域（如：办公室健身小C）",
            "创意昵称+emoji（如：肌肤守护者🛡️）",
            "故事化昵称（如：深夜健身房）",
            "专业度+领域（如：认证香水师）"
        ]
        
        bio_features = [
            "数据化承诺（8年经验|100+产品测评）",
            "专业身份认证（XX大学|XX证书持有者）",
            "内容预期（每周X更新|干货分享）",
            "个性化标语（拒绝虚假种草|只分享真实体验）",
            "互动引导（关注我了解更多|评论区告诉我你想看什么）"
        ]
        
        account_type = random.choice(account_types)
        selected_name_structures = random.sample(name_structures, 2)
        selected_bio_features = random.sample(bio_features, 3)
        
        return {
            "account_id": account_id,
            "account_type": account_type,
            "name_structure_analysis": selected_name_structures,
            "bio_features": selected_bio_features,
            "recommendation": f"建议采用{account_type}定位，使用{selected_name_structures[0]}命名结构，简介中加入{selected_bio_features[0]}元素提升专业感"
        }
    
    async def _arun(self, account_id: str) -> Dict[str, Any]:
        """异步执行获取账号信息"""
        raise NotImplementedError("暂不支持异步操作")

class GetSearchKeywordTool(BaseTool):
    """获取关键词联想词工具"""
    name: str = "get_search_keyword"
    description: str = "获取核心关键词的相关联想词，如获取'职场健身'相关联想词（'通勤拉伸'、'久坐护腰'等），优化账号标签体系"
    args_schema: Type[BaseModel] = SearchKeywordInput
    
    def _run(self, keyword: str) -> Dict[str, Any]:
        """
        获取搜索关键词的联想词
        
        Args:
            keyword: 核心关键词
            
        Returns:
            Dict: 关键词相关联想词和分析
        """
        # 模拟API返回关键词联想分析
        keyword_categories = {
            "护肤": ["敏感肌护肤", "油皮护肤", "抗老护肤", "美白护肤", "保湿补水"],
            "健身": ["居家健身", "办公室健身", "增肌健身", "减脂健身", "通勤健身"],
            "美食": ["家常菜谱", "减脂餐", "下午茶", "早餐食谱", "快手料理"],
            "穿搭": ["日常穿搭", "职场穿搭", "约会穿搭", "轻奢穿搭", "显瘦穿搭"]
        }
        
        # 决定使用哪个类别的关键词
        category = None
        for cat, keywords in keyword_categories.items():
            if keyword.lower() in cat.lower():
                category = cat
                break
        
        # 如果找不到匹配的类别，使用默认类别
        if not category:
            category = random.choice(list(keyword_categories.keys()))
        
        # 获取相关联想词
        related_keywords = keyword_categories[category]
        search_volume = [random.randint(1000, 50000) for _ in range(len(related_keywords))]
        
        # 创建排序后的关键词和搜索量的列表
        keyword_data = list(zip(related_keywords, search_volume))
        keyword_data.sort(key=lambda x: x[1], reverse=True)
        
        top_keywords = [k for k, _ in keyword_data[:3]]
        
        return {
            "core_keyword": keyword,
            "related_keywords": related_keywords,
            "search_volume": dict(zip(related_keywords, search_volume)),
            "top_recommendations": top_keywords,
            "analysis": f"搜索'{keyword}'的用户多关注'{top_keywords[0]}'和'{top_keywords[1]}'相关内容，建议在账号标签和内容中加入这些关键词以提高曝光"
        }
    
    async def _arun(self, keyword: str) -> Dict[str, Any]:
        """异步执行获取关键词联想词"""
        raise NotImplementedError("暂不支持异步操作")

class SearchUserTool(BaseTool):
    """搜索同领域账号工具"""
    name: str = "search_user"
    description: str = "搜索同领域账号，如搜索'职场健身'标签下的前20名账号，分析人设同质化问题"
    args_schema: Type[BaseModel] = SearchUserInput
    
    def _run(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        """
        搜索同领域账号
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果限制
            
        Returns:
            Dict: 账号列表和分析
        """
        # 模拟API返回搜索结果
        results = []
        persona_keywords = [
            "专业", "达人", "博主", "教练", "老师", "测评师", "种草官", "创作者", 
            "生活家", "设计师", "玩家", "健身达人", "搭配师", "美妆博主"
        ]
        
        for i in range(limit):
            persona_type = random.choice(persona_keywords)
            follower_count = random.randint(1000, 500000)
            
            results.append({
                "user_id": f"user_{i}_{keyword.replace(' ', '_')}",
                "nickname": f"{keyword}{persona_type}{i+1}号",
                "follower_count": follower_count,
                "notes_count": random.randint(50, 300),
                "persona_keywords": random.sample(persona_keywords, 3),
                "description": f"专注于{keyword}内容分享" if i % 3 != 0 else f"{keyword}领域创作者，提供专业{keyword}指导"
            })
        
        # 按粉丝数排序
        results.sort(key=lambda x: x["follower_count"], reverse=True)
        
        # 分析人设同质化问题
        common_keywords = set()
        for result in results[:5]:  # 只分析前5个账号
            common_keywords.update(result["persona_keywords"])
        
        return {
            "accounts": results,
            "analysis": {
                "total_found": len(results),
                "common_persona_keywords": list(common_keywords),
                "homogenization_issues": f"在{keyword}领域前20名账号中，{round(len(results) * 0.7)}个使用类似人设定位，建议避免使用{list(common_keywords)[:3]}等高频人设关键词，寻找差异化定位"
            }
        }
    
    async def _arun(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        """异步执行搜索同领域账号"""
        raise NotImplementedError("暂不支持异步操作")

class GetUserAllNotesTool(BaseTool):
    """获取用户所有笔记工具"""
    name: str = "get_user_all_notes"
    description: str = "提取竞品笔记内容，识别高频出现的人设关键词（如'专业教练'、'宝妈'），避免定位重复"
    args_schema: Type[BaseModel] = UserAllNotesInput
    
    def _run(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        获取用户所有笔记
        
        Args:
            user_id: 用户ID
            limit: 返回结果限制
            
        Returns:
            Dict: 包含笔记列表和分析
        """
        # 模拟笔记主题
        topics = ["产品测评", "使用教程", "经验分享", "问题解决", "新品推荐", "科普知识", "趋势分析"]
        
        # 模拟笔记格式
        formats = ["图文测评", "视频记录", "清单总结", "问答解析", "步骤教程", "对比分析"]
        
        # 生成随机笔记数据
        notes = []
        for i in range(limit):
            topic = random.choice(topics)
            note_format = random.choice(formats)
            
            notes.append({
                "note_id": f"note_{i}_{user_id}",
                "title": f"{topic}：{note_format}{i+1}",
                "type": "图文" if random.random() > 0.3 else "视频",
                "likes": random.randint(10, 5000),
                "comments": random.randint(0, 200),
                "collects": random.randint(5, 500),
                "create_time": f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}",
                "topic": topic,
                "format": note_format
            })
        
        # 分析主题分布
        topic_distribution = {}
        for note in notes:
            topic = note["topic"]
            topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
        
        # 转换为百分比
        for topic in topic_distribution:
            topic_distribution[topic] = round(topic_distribution[topic] / len(notes) * 100)
        
        # 分析高频人设关键词
        format_distribution = {}
        for note in notes:
            format_name = note["format"]
            format_distribution[format_name] = format_distribution.get(format_name, 0) + 1
        
        return {
            "user_id": user_id,
            "notes_count": len(notes),
            "notes": notes,
            "analysis": {
                "topic_distribution": topic_distribution,
                "format_distribution": format_distribution,
                "top_performing_topics": [k for k, v in sorted(topic_distribution.items(), key=lambda item: item[1], reverse=True)][:3],
                "persona_keywords": ["专业", "实用", "深度" if random.random() > 0.5 else "通俗易懂"],
                "content_focus": f"内容{round(topic_distribution.get('产品测评', 0) + topic_distribution.get('经验分享', 0))}%集中在产品测评和经验分享，建议开拓更多{random.choice(list(set(topics) - {'产品测评', '经验分享'}))}类内容"
            }
        }
    
    async def _arun(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """异步执行获取用户所有笔记"""
        raise NotImplementedError("暂不支持异步操作")

class GetHomefeedRecommendTool(BaseTool):
    """获取首页推荐内容工具"""
    name: str = "get_homefeed_recommend_by_num"
    description: str = "获取指定品类的热门推荐笔记，如获取健身频道Top50推荐笔记，分析近期爆款内容形式"
    args_schema: Type[BaseModel] = HomefeedRecommendInput
    
    def _run(self, category: str, num: int = 50) -> Dict[str, Any]:
        """
        获取首页推荐内容
        
        Args:
            category: 内容品类
            num: 返回结果数量
            
        Returns:
            Dict: 推荐内容列表和分析
        """
        # 内容形式列表
        content_forms = [
            "问题-解决方案图文", "步骤分解图文", "对比图文", "清单型图文", 
            "跟练视频", "Vlog视频", "测评视频", "知识点讲解视频"
        ]
        
        # 生成随机推荐内容
        recommendations = []
        for i in range(num):
            content_form = random.choice(content_forms)
            is_video = "视频" in content_form
            
            recommendations.append({
                "note_id": f"note_{i}_{category.replace(' ', '_')}",
                "title": f"{random.choice(['如何', '为什么', '这样做', '必看'])}：{category}{content_form}内容{i+1}",
                "type": "视频" if is_video else "图文",
                "likes": random.randint(500, 50000),
                "comments": random.randint(10, 2000),
                "collects": random.randint(100, 10000),
                "create_time": f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}",
                "content_form": content_form,
                "has_purchase": random.choice([True, False, False, False])  # 25%概率有购物链接
            })
        
        # 按互动量排序
        recommendations.sort(key=lambda x: x["likes"] + x["comments"]*3 + x["collects"]*2, reverse=True)
        
        # 分析内容形式分布
        form_distribution = {}
        for rec in recommendations:
            form = rec["content_form"]
            form_distribution[form] = form_distribution.get(form, 0) + 1
        
        # 转换为百分比
        for form in form_distribution:
            form_distribution[form] = round(form_distribution[form] / len(recommendations) * 100)
        
        # 分析视频与图文比例
        video_count = sum(1 for rec in recommendations if rec["type"] == "视频")
        video_percentage = round(video_count / len(recommendations) * 100)
        
        # 分析标题特征
        title_features = []
        if any("如何" in rec["title"] for rec in recommendations[:10]):
            title_features.append("问题解决型")
        if any("必看" in rec["title"] for rec in recommendations[:10]):
            title_features.append("强调重要性")
        if any(str(n) in rec["title"] for n in range(1, 10) for rec in recommendations[:10]):
            title_features.append("数字引导型")
        
        return {
            "category": category,
            "total_recommendations": len(recommendations),
            "top_recommendations": recommendations[:10],
            "analysis": {
                "content_form_distribution": form_distribution,
                "video_percentage": video_percentage,
                "image_text_percentage": 100 - video_percentage,
                "title_features": title_features,
                "trending_forms": [k for k, v in sorted(form_distribution.items(), key=lambda item: item[1], reverse=True)][:3],
                "insight": f"在{category}品类中，{[k for k, v in sorted(form_distribution.items(), key=lambda item: item[1], reverse=True)][0]}最受欢迎，占比{form_distribution[[k for k, v in sorted(form_distribution.items(), key=lambda item: item[1], reverse=True)][0]]}%，建议优先采用此内容形式"
            }
        }
    
    async def _arun(self, category: str, num: int = 50) -> Dict[str, Any]:
        """异步执行获取首页推荐内容"""
        raise NotImplementedError("暂不支持异步操作")

class SearchNoteTool(BaseTool):
    """搜索笔记工具"""
    name: str = "search_note"
    description: str = "按关键词搜索笔记，如按'职场健身'搜索近30天内容，筛选出点赞>5000的笔记，提炼高频选题"
    args_schema: Type[BaseModel] = SearchNoteInput
    
    def _run(self, keyword: str, days: int = 30, min_likes: int = 0, sort_by: str = "hot") -> Dict[str, Any]:
        """
        搜索笔记
        
        Args:
            keyword: 搜索关键词
            days: 限定天数范围
            min_likes: 最小点赞数
            sort_by: 排序方式，hot或time
            
        Returns:
            Dict: 笔记列表和分析
        """
        # 生成随机搜索结果
        num_results = random.randint(30, 100)
        results = []
        
        # 常见标题结构
        title_structures = [
            "数字+痛点+解决方案",
            "疑问句+答案暗示",
            "强调词+核心利益点",
            "紧急感+关键结果",
            "对比型+转折"
        ]
        
        # 内容类型
        content_types = ["教程", "分享", "测评", "记录", "总结", "攻略"]
        
        # 生成搜索结果
        for i in range(num_results):
            likes = random.randint(10, 20000)
            if likes < min_likes:
                likes = min_likes + random.randint(0, 1000)
                
            content_type = random.choice(content_types)
            title_structure = random.choice(title_structures)
            
            # 根据标题结构生成标题
            if "数字" in title_structure:
                title = f"{random.randint(1, 10)}个{keyword}{content_type}方法"
            elif "疑问句" in title_structure:
                title = f"如何掌握{keyword}的{content_type}技巧？"
            elif "强调词" in title_structure:
                title = f"必学！{keyword}{content_type}绝技"
            elif "紧急感" in title_structure:
                title = f"速收藏！{keyword}高效{content_type}"
            else:
                title = f"以前vs现在：{keyword}{content_type}新方法"
            
            results.append({
                "note_id": f"note_search_{i}",
                "title": title,
                "type": "视频" if random.random() > 0.6 else "图文",
                "likes": likes,
                "comments": random.randint(5, min(likes//2, 1000)),
                "collects": random.randint(10, min(likes//1.5, 2000)),
                "create_time": f"2023-{random.randint(1, 12)}-{random.randint(1, 28)}",
                "content_type": content_type,
                "title_structure": title_structure
            })
        
        # 按点赞数排序
        if sort_by == "hot":
            results.sort(key=lambda x: x["likes"], reverse=True)
        else:
            # 按时间排序，这里简单模拟
            random.shuffle(results)
        
        # 筛选满足点赞要求的笔记
        filtered_results = [r for r in results if r["likes"] >= min_likes]
        
        # 分析高频选题
        topic_count = {}
        for result in filtered_results:
            topic = result["content_type"]
            topic_count[topic] = topic_count.get(topic, 0) + 1
        
        # 分析标题结构
        structure_count = {}
        for result in filtered_results:
            structure = result["title_structure"]
            structure_count[structure] = structure_count.get(structure, 0) + 1
        
        return {
            "keyword": keyword,
            "days_range": days,
            "min_likes": min_likes,
            "total_results": len(filtered_results),
            "notes": filtered_results[:20],  # 只返回前20条结果
            "analysis": {
                "popular_topics": {k: round(v/len(filtered_results)*100) for k, v in sorted(topic_count.items(), key=lambda item: item[1], reverse=True)},
                "effective_title_structures": {k: round(v/len(filtered_results)*100) for k, v in sorted(structure_count.items(), key=lambda item: item[1], reverse=True)},
                "high_engagement_topics": [k for k, v in sorted(topic_count.items(), key=lambda item: item[1], reverse=True)][:3],
                "recommendation": f"建议优先创作{[k for k, v in sorted(topic_count.items(), key=lambda item: item[1], reverse=True)][0]}类型内容，使用{[k for k, v in sorted(structure_count.items(), key=lambda item: item[1], reverse=True)][0]}标题结构，可显著提高内容曝光度"
            }
        }
    
    async def _arun(self, keyword: str, days: int = 30, min_likes: int = 0, sort_by: str = "hot") -> Dict[str, Any]:
        """异步执行搜索笔记"""
        raise NotImplementedError("暂不支持异步操作")

class GetNoteInfoTool(BaseTool):
    """获取笔记详情工具"""
    name: str = "get_note_info"
    description: str = "解析单篇爆款笔记的标题结构和互动数据，提炼可复用的创作模板"
    args_schema: Type[BaseModel] = NoteInfoInput
    
    def _run(self, note_id: str) -> Dict[str, Any]:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
            
        Returns:
            Dict: 笔记详情
        """
        # 模拟笔记详情
        note_type = "视频" if random.random() > 0.6 else "图文"
        likes = random.randint(500, 50000)
        
        # 标题结构类型
        title_structures = {
            "数字引导型": f"{random.randint(1, 10)}个小技巧让你轻松掌握",
            "问题解决型": "如何解决长久困扰的问题？",
            "利益暗示型": "学会这个技巧，效率提升300%",
            "紧急感型": "必看！这些错误你一定在犯",
            "对比转折型": "对比：从入门到精通的蜕变"
        }
        
        structure_type = random.choice(list(title_structures.keys()))
        title = title_structures[structure_type]
        
        # 内容结构
        content_structure = {
            "引言": "点明痛点，引发共鸣",
            "主体": "分步骤/分点展示核心内容",
            "结尾": "总结要点，引导互动/关注"
        }
        
        # 互动数据
        interaction_data = {
            "likes": likes,
            "comments": random.randint(10, min(likes//3, 2000)),
            "collects": random.randint(50, min(likes//2, 5000)),
            "shares": random.randint(5, min(likes//4, 1000))
        }
        
        # 用户评论关键词
        comment_keywords = ["实用", "干货", "学到了", "感谢分享", "收藏了"]
        
        return {
            "note_id": note_id,
            "title": title,
            "title_structure": structure_type,
            "type": note_type,
            "content_structure": content_structure,
            "interaction_data": interaction_data,
            "comment_keywords": random.sample(comment_keywords, 3),
            "analysis": {
                "engagement_rate": round((interaction_data["comments"] + interaction_data["shares"]) / interaction_data["likes"] * 100),
                "collection_rate": round(interaction_data["collects"] / interaction_data["likes"] * 100),
                "title_effectiveness": "高" if interaction_data["likes"] > 5000 else "中",
                "recommended_improvement": f"建议在{random.choice(['标题', '开头', '结尾'])}增加{random.choice(['用户引导', '数据支持', '情感共鸣'])}元素，提升互动率"
            }
        }
    
    async def _arun(self, note_id: str) -> Dict[str, Any]:
        """异步执行获取笔记详情"""
        raise NotImplementedError("暂不支持异步操作")

class GetNoteNoWaterVideoTool(BaseTool):
    """获取无水印视频工具"""
    name: str = "get_note_no_water_video"
    description: str = "解析爆款视频笔记的无水印链接，用于二次创作参考"
    args_schema: Type[BaseModel] = NoWaterVideoInput
    
    def _run(self, note_id: str) -> Dict[str, Any]:
        """
        获取笔记无水印视频链接
        
        Args:
            note_id: 笔记ID
            
        Returns:
            Dict: 无水印视频信息
        """
        return {
            "note_id": note_id,
            "video_url": f"https://example.com/xhs/video/{note_id}.mp4",
            "duration": random.randint(15, 180),
            "resolution": random.choice(["1080p", "720p"]),
            "message": "视频链接已生成，仅供学习参考"
        }
    
    async def _arun(self, note_id: str) -> Dict[str, Any]:
        """异步执行获取无水印视频"""
        raise NotImplementedError("暂不支持异步操作")

# 辅助方法，创建工具集合
def get_account_profile_tools() -> List[BaseTool]:
    """获取账号人设相关工具集合"""
    return [
        GetUserInfoTool(),
        GetSearchKeywordTool()
    ]

def get_persona_builder_tools() -> List[BaseTool]:
    """获取人设构建相关工具集合"""
    return [
        SearchUserTool(),
        GetUserAllNotesTool()
    ]

def get_content_planner_tools() -> List[BaseTool]:
    """获取内容规划相关工具集合"""
    return [
        GetHomefeedRecommendTool(),
        SearchNoteTool()
    ]

def get_platform_trend_tools() -> List[BaseTool]:
    """获取平台趋势分析相关工具集合"""
    return [
        GetHomefeedRecommendTool(),
        SearchNoteTool()
    ]

def get_content_style_tools() -> List[BaseTool]:
    """获取内容风格分析相关工具集合"""
    return [
        GetUserAllNotesTool(),
        GetNoteInfoTool()
    ]

def get_content_creator_tools() -> List[BaseTool]:
    """获取内容创作相关工具集合"""
    return [
        GetNoteNoWaterVideoTool(),
        GetNoteInfoTool()
    ]
