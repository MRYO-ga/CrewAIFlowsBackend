# 智能数据服务模块 - AI驱动的数据获取和优化系统

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from .mcp_data_service import mcp_data_service
from .myLLM import chat_with_llm

logger = logging.getLogger(__name__)

class IntelligentDataService:
    """智能数据服务类 - 基于AI的数据分析和优化系统"""
    
    def __init__(self):
        self.mcp_service = mcp_data_service
    
    def analyze_user_context(self, user_id: str, intent: str) -> Dict[str, Any]:
        """
        分析用户上下文，智能获取相关数据
        
        Args:
            user_id: 用户ID  
            intent: 用户意图/需求
            
        Returns:
            Dict[str, Any]: 分析结果和相关数据
        """
        try:
            # 根据意图判断需要获取的数据类型
            required_data_types = self._determine_required_data(intent)
            
            # 获取用户的历史数据
            user_context = {}
            
            if "account_info" in required_data_types:
                user_context["account_info"] = self._get_account_context(user_id)
            
            if "competitor_analysis" in required_data_types:
                user_context["competitor_analysis"] = self._get_competitor_context(user_id)
            
            if "content_library" in required_data_types:
                user_context["content_library"] = self._get_content_context(user_id)
            
            if "publish_schedule" in required_data_types:
                user_context["publish_schedule"] = self._get_schedule_context(user_id)
            
            # 使用AI分析上下文数据
            analysis_result = self._ai_analyze_context(intent, user_context)
            
            return {
                "intent": intent,
                "user_context": user_context,
                "analysis": analysis_result,
                "recommendations": self._generate_recommendations(intent, user_context, analysis_result)
            }
            
        except Exception as e:
            logger.error(f"分析用户上下文失败: {e}")
            return {
                "intent": intent,
                "error": str(e),
                "fallback_data": self._get_fallback_data(intent)
            }
    
    def _determine_required_data(self, intent: str) -> List[str]:
        """根据用户意图判断需要获取的数据类型"""
        intent_lower = intent.lower()
        required_data = []
        
        # 账号优化相关
        if any(keyword in intent_lower for keyword in ["账号", "人设", "简介", "头像", "基础信息"]):
            required_data.extend(["account_info", "competitor_analysis"])
        
        # 内容相关
        if any(keyword in intent_lower for keyword in ["内容", "文案", "标题", "创作", "素材"]):
            required_data.extend(["content_library", "competitor_analysis"])
        
        # 发布计划相关
        if any(keyword in intent_lower for keyword in ["发布", "计划", "时间", "频率", "安排"]):
            required_data.extend(["publish_schedule", "content_library"])
        
        # 竞品分析相关
        if any(keyword in intent_lower for keyword in ["竞品", "对手", "分析", "学习", "参考"]):
            required_data.append("competitor_analysis")
        
        # 如果没有明确意图，获取基础数据
        if not required_data:
            required_data = ["account_info"]
        
        return list(set(required_data))
    
    def _get_account_context(self, user_id: str) -> Dict[str, Any]:
        """获取账号上下文信息"""
        account_info = self.mcp_service.get_account_info(user_id)
        
        # 模拟获取更详细的账号信息
        enhanced_account_info = {
            **account_info,
            "performance_metrics": {
                "avg_likes_per_post": 580,
                "avg_comments_per_post": 45,
                "engagement_rate": 6.8,
                "follower_growth_rate": 2.3,
                "best_performing_content_types": ["产品测评", "护肤心得"]
            },
            "improvement_areas": [
                "发布频率可以提高到每周4-5次",
                "标题可以更具吸引力",
                "互动回复时效可以提升"
            ]
        }
        
        return enhanced_account_info
    
    def _get_competitor_context(self, user_id: str) -> List[Dict[str, Any]]:
        """获取竞品分析上下文"""
        # 模拟竞品分析数据
        competitors = [
            {
                "name": "水北山南",
                "follower_count": "128.6w",
                "category": "文艺美妆",
                "strengths": ["文字功底强", "内容有深度", "粉丝黏性高"],
                "successful_strategies": [
                    "用情感化的文字建立连接",
                    "分享真实的生活体验",
                    "定期的深度内容分享"
                ],
                "content_analysis": {
                    "avg_post_length": 800,
                    "popular_tags": ["INFJ", "文字疗愈", "生活美学"],
                    "posting_pattern": "每周2-3次，晚上8-10点"
                }
            },
            {
                "name": "美妆情报局",
                "follower_count": "328.5w",
                "category": "美妆测评",
                "strengths": ["专业性强", "测评详细", "更新稳定"],
                "successful_strategies": [
                    "专业的产品测评方法",
                    "详细的使用体验分享",
                    "定期的新品测试"
                ],
                "content_analysis": {
                    "avg_post_length": 600,
                    "popular_tags": ["测评", "种草", "美妆榜"],
                    "posting_pattern": "每周4-5次，中午12点和晚上9点"
                }
            }
        ]
        
        return competitors
    
    def _get_content_context(self, user_id: str) -> List[Dict[str, Any]]:
        """获取内容库上下文"""
        # 模拟内容库数据
        contents = [
            {
                "title": "平价控油散粉测评｜学生党必看",
                "status": "draft",
                "content_type": "image_text",
                "performance_prediction": {
                    "estimated_views": 3500,
                    "estimated_likes": 210,
                    "confidence": 0.75
                },
                "optimization_suggestions": [
                    "标题可以加上具体价格范围",
                    "增加对比图表",
                    "添加使用心得分享"
                ]
            },
            {
                "title": "新手化妆教程｜5分钟打造清透妆容",
                "status": "scheduled",
                "content_type": "video",
                "performance_prediction": {
                    "estimated_views": 8000,
                    "estimated_likes": 560,
                    "confidence": 0.82
                },
                "optimization_suggestions": [
                    "可以制作分步骤的图文版本",
                    "添加产品清单",
                    "增加常见问题解答"
                ]
            }
        ]
        
        return contents
    
    def _get_schedule_context(self, user_id: str) -> List[Dict[str, Any]]:
        """获取发布计划上下文"""
        # 模拟发布计划数据
        schedules = [
            {
                "title": "春季护肤专题发布计划",
                "type": "batch",
                "status": "pending",
                "publish_time": (datetime.now() + timedelta(days=2)).isoformat(),
                "expected_performance": {
                    "total_estimated_views": 15000,
                    "target_engagement_rate": 6.5
                },
                "optimization_suggestions": [
                    "建议调整到晚上8-9点发布",
                    "可以增加互动引导内容"
                ]
            }
        ]
        
        return schedules
    
    def _ai_analyze_context(self, intent: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI分析用户上下文数据"""
        # 构建AI分析提示词
        analysis_prompt = f"""
        作为小红书运营专家，请分析以下用户数据并提供专业建议：
        
        用户需求：{intent}
        
        用户数据：
        {json.dumps(user_context, ensure_ascii=False, indent=2)}
        
        请从以下角度进行分析：
        1. 当前状况评估
        2. 主要问题识别
        3. 改进机会分析
        4. 具体优化建议
        
        请以JSON格式返回分析结果：
        {{
            "current_status": "当前状况评估",
            "key_issues": ["问题1", "问题2"],
            "opportunities": ["机会1", "机会2"],
            "specific_suggestions": ["建议1", "建议2"]
        }}
        """
        
        try:
            # 调用AI进行分析
            messages = [
                {"role": "system", "content": "你是一个专业的小红书运营分析师，擅长数据分析和策略建议。"},
                {"role": "user", "content": analysis_prompt}
            ]
            
            ai_response = chat_with_llm(messages, llmType="openai", model="gpt-4o")
            
            # 解析AI响应
            try:
                response_data = json.loads(ai_response)
                if "reply" in response_data:
                    # 从回复中提取JSON
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', response_data["reply"])
                    if json_match:
                        analysis_result = json.loads(json_match.group())
                    else:
                        analysis_result = {"analysis": response_data["reply"]}
                else:
                    analysis_result = response_data
                
                return analysis_result
                
            except json.JSONDecodeError:
                return {"analysis": ai_response}
                
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return {"error": f"AI分析失败: {e}"}
    
    def _generate_recommendations(self, intent: str, user_context: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成具体的优化建议"""
        recommendations = []
        
        # 基于意图和分析结果生成建议
        if "账号" in intent or "人设" in intent:
            recommendations.append({
                "type": "account_optimization",
                "title": "账号基础信息优化",
                "priority": "high",
                "actions": [
                    "优化个人简介，突出核心价值主张",
                    "更新头像和背景图，提升视觉识别度", 
                    "完善人设标签，明确目标受众"
                ],
                "expected_impact": "提升账号专业度和吸引力，预计粉丝增长率提升15-20%"
            })
        
        if "内容" in intent:
            recommendations.append({
                "type": "content_optimization",
                "title": "内容策略优化",
                "priority": "high",
                "actions": [
                    "结合竞品分析调整内容方向",
                    "优化标题和标签使用",
                    "增加互动引导元素"
                ],
                "expected_impact": "提升内容曝光度和互动率，预计平均点赞数提升30%"
            })
        
        if "发布" in intent:
            recommendations.append({
                "type": "publishing_optimization", 
                "title": "发布策略优化",
                "priority": "medium",
                "actions": [
                    "调整发布时间到用户活跃高峰期",
                    "制定稳定的发布频率",
                    "设置A/B测试验证效果"
                ],
                "expected_impact": "提升内容初期曝光，预计整体互动率提升25%"
            })
        
        return recommendations
    
    def _get_fallback_data(self, intent: str) -> Dict[str, Any]:
        """获取默认的回退数据"""
        return {
            "message": "获取了基础的账号信息和建议",
            "basic_suggestions": [
                "定期更新内容，保持活跃度",
                "关注热门话题和趋势",
                "积极与粉丝互动"
            ]
        }
    
    def optimize_account_info(self, user_id: str, optimization_type: str = "comprehensive") -> Dict[str, Any]:
        """
        智能优化账号基础信息
        
        Args:
            user_id: 用户ID
            optimization_type: 优化类型 (comprehensive, bio, tags, strategy)
            
        Returns:
            Dict[str, Any]: 优化建议和新的账号信息
        """
        # 获取当前账号信息
        current_account = self._get_account_context(user_id)
        
        # 获取竞品分析数据作为参考
        competitors = self._get_competitor_context(user_id)
        
        # 使用AI生成优化建议
        optimization_prompt = f"""
        作为小红书账号优化专家，请基于以下信息为用户提供账号优化建议：
        
        当前账号信息：
        {json.dumps(current_account, ensure_ascii=False, indent=2)}
        
        竞品参考：
        {json.dumps(competitors, ensure_ascii=False, indent=2)}
        
        优化重点：{optimization_type}
        
        请提供：
        1. 优化后的个人简介
        2. 建议的标签定位
        3. 内容策略建议
        4. 具体的改进措施
        
        以JSON格式返回：
        {{
            "optimized_bio": "优化后的个人简介",
            "recommended_tags": ["标签1", "标签2", "标签3"],
            "content_strategy": "内容策略建议",
            "improvement_actions": ["行动1", "行动2", "行动3"],
            "expected_results": "预期效果说明"
        }}
        """
        
        try:
            messages = [
                {"role": "system", "content": "你是一个专业的小红书账号优化师，擅长账号定位和内容策略。"},
                {"role": "user", "content": optimization_prompt}
            ]
            
            ai_response = chat_with_llm(messages, llmType="openai", model="gpt-4o")
            
            # 解析AI响应
            try:
                response_data = json.loads(ai_response)
                if "reply" in response_data:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', response_data["reply"])
                    if json_match:
                        optimization_result = json.loads(json_match.group())
                    else:
                        optimization_result = {"suggestions": response_data["reply"]}
                else:
                    optimization_result = response_data
                
                return {
                    "current_account": current_account,
                    "optimization_result": optimization_result,
                    "timestamp": datetime.now().isoformat()
                }
                
            except json.JSONDecodeError:
                return {
                    "current_account": current_account,
                    "suggestions": ai_response,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"账号优化失败: {e}")
            return {
                "current_account": current_account,
                "error": str(e),
                "fallback_suggestions": [
                    "完善个人简介，突出专业特色",
                    "优化标签使用，提高可发现性",
                    "制定清晰的内容策略"
                ]
            }

# 全局实例
intelligent_data_service = IntelligentDataService() 