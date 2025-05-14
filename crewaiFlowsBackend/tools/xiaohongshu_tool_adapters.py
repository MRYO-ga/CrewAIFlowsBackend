from typing import Dict, Any, List
from .xiaohongshu_tools import (
    XiaoHongShuAccountTool, 
    GetUserInfoTool,
    GetSearchKeywordTool,
    SearchUserTool,
    GetUserAllNotesTool,
    GetHomefeedRecommendTool,
    SearchNoteTool,
    GetNoteInfoTool,
    GetNoteNoWaterVideoTool,
    get_account_profile_tools,
    get_persona_builder_tools,
    get_content_planner_tools,
    get_platform_trend_tools,
    get_content_style_tools,
    get_content_creator_tools
)

class XiaoHongShuToolAdapters:
    """
    小红书工具适配器，将原生工具方法转换为CrewAI能使用的工具格式
    """
    
    def __init__(self):
        """初始化适配器"""
        self.xhs_tools = XiaoHongShuAccountTool()
        
    def get_account_info_tool(self) -> Any:
        """获取账号信息工具"""
        # 暂时移除此工具，需要重新实现为BaseTool子类
        return None
        
    def get_user_info_tool(self) -> Any:
        """分析对标账号名称/简介结构工具"""
        return GetUserInfoTool()
        
    def get_search_keyword_tool(self) -> Any:
        """获取关键词联想词工具"""
        return GetSearchKeywordTool()
        
    def search_user_tool(self) -> Any:
        """搜索同领域账号工具"""
        return SearchUserTool()
        
    def get_user_all_notes_tool(self) -> Any:
        """获取用户所有笔记工具"""
        return GetUserAllNotesTool()
        
    def get_homefeed_recommend_tool(self) -> Any:
        """获取首页推荐内容工具"""
        return GetHomefeedRecommendTool()
        
    def search_note_tool(self) -> Any:
        """搜索笔记工具"""
        return SearchNoteTool()
        
    def get_note_info_tool(self) -> Any:
        """获取笔记详情工具"""
        return GetNoteInfoTool()
        
    def get_note_no_water_video_tool(self) -> Any:
        """获取无水印视频工具"""
        return GetNoteNoWaterVideoTool()
        
    def get_account_profile_tools(self) -> List[Any]:
        """获取账号人设相关工具集合"""
        return get_account_profile_tools()
        
    def get_persona_builder_tools(self) -> List[Any]:
        """获取人设构建相关工具集合"""
        return get_persona_builder_tools()
        
    def get_content_planner_tools(self) -> List[Any]:
        """获取内容规划相关工具集合"""
        return get_content_planner_tools()
        
    def get_platform_trend_tools(self) -> List[Any]:
        """获取平台趋势分析相关工具集合"""
        return get_platform_trend_tools()
        
    def get_content_style_tools(self) -> List[Any]:
        """获取内容风格分析相关工具集合"""
        return get_content_style_tools()
        
    def get_content_creator_tools(self) -> List[Any]:
        """获取内容创作相关工具集合"""
        return get_content_creator_tools() 