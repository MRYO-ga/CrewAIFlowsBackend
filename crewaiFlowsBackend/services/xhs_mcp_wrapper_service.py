#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书MCP包装器服务
在调用小红书MCP工具时自动保存数据到数据库
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .xhs_service import XhsService
from .mcp_client_service import MCPToolResult

logger = logging.getLogger(__name__)


class XhsMCPWrapperService:
    """小红书MCP包装器服务类"""
    
    def __init__(self):
        self.xhs_service = XhsService()
        self.logger = logging.getLogger(__name__)
        
        # 小红书相关的工具名称
        self.xhs_tools = {
            'home_feed': '获取首页推荐笔记',
            'search_notes': '根据关键词搜索笔记',
            'get_note_content': '获取笔记内容',
            'get_note_comments': '获取笔记评论',
            # 'post_comment': '发布评论到指定笔记'
        }
    
    def is_xhs_tool(self, tool_name: str) -> bool:
        """判断是否是小红书相关工具"""
        return tool_name in self.xhs_tools
    
    def _clean_tool_args(self, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """清理工具参数，移除不能序列化的对象"""
        cleaned_args = {}
        for key, value in tool_args.items():
            # 跳过不能序列化的对象
            if key in ['run_manager', 'config']:
                continue
            # 只保留基本数据类型
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                cleaned_args[key] = value
            else:
                # 对于其他类型，转换为字符串
                cleaned_args[key] = str(value)
        return cleaned_args
    
    async def wrap_tool_call(self, tool_name: str, tool_args: Dict[str, Any], 
                           original_result: MCPToolResult) -> MCPToolResult:
        """
        包装工具调用，添加数据保存功能
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            original_result: 原始工具调用结果
            
        Returns:
            处理后的工具调用结果
        """
        start_time = time.time()
        
        print(f"🔍 [XHS包装器] 开始处理工具调用")
        print(f"   工具名称: {tool_name}")
        print(f"   工具参数: {self._clean_tool_args(tool_args)}")
        print(f"   是否小红书工具: {self.is_xhs_tool(tool_name)}")
        
        try:
            if not self.is_xhs_tool(tool_name):
                # 不是小红书工具，直接返回原始结果
                print(f"⏭️ [XHS包装器] 非小红书工具，直接返回原始结果")
                return original_result
            
            print(f"🔄 [XHS包装器] 开始处理小红书工具调用: {tool_name}")
            
            # 解析原始结果
            result_content = original_result.content
            print(f"📝 [XHS包装器] 原始结果类型: {type(result_content)}")
            print(f"📝 [XHS包装器] 原始结果前100字符: {str(result_content)[:100]}...")
            
            if isinstance(result_content, str):
                # 如果是字符串，尝试解析为JSON
                try:
                    # 检查是否包含JSON数据
                    if result_content.startswith('{') or result_content.startswith('['):
                        api_response = json.loads(result_content)
                        print(f"✅ [XHS包装器] 成功解析JSON格式数据")
                    else:
                        # 如果不是JSON格式，可能是文本结果，不需要保存到数据库
                        print(f"📄 [XHS包装器] 工具 {tool_name} 返回文本结果，不保存到数据库")
                        return original_result
                except json.JSONDecodeError as e:
                    print(f"❌ [XHS包装器] JSON解析失败: {e}")
                    print(f"❌ [XHS包装器] 工具 {tool_name} 返回非JSON格式结果，不保存到数据库")
                    return original_result
            elif isinstance(result_content, dict):
                api_response = result_content
                print(f"✅ [XHS包装器] 结果已是字典格式")
            else:
                print(f"⚠️ [XHS包装器] 工具 {tool_name} 返回未知格式结果: {type(result_content)}")
                return original_result
            
            # 清理工具参数，移除不能序列化的对象
            cleaned_tool_args = self._clean_tool_args(tool_args)
            
            # 根据工具类型处理数据保存
            print(f"💾 [XHS包装器] 开始保存数据...")
            print(f"💾 [XHS包装器] API响应数据键: {list(api_response.keys()) if isinstance(api_response, dict) else '非字典类型'}")
            
            saved_data = await self._save_tool_data(tool_name, cleaned_tool_args, api_response)
            print(f"💾 [XHS包装器] 数据保存结果: {saved_data}")
            
            # 记录API调用日志
            response_time = time.time() - start_time
            print(f"📊 [XHS包装器] 开始记录API调用日志...")
            api_log_result = await self.xhs_service.save_api_log(
                api_name=tool_name,
                request_params=cleaned_tool_args,  # 使用清理后的参数
                response_data=api_response,
                response_time=response_time,
                success=True
            )
            print(f"📊 [XHS包装器] API日志保存结果: {api_log_result}")
            
            # 为AI提供精简的数据（移除URL、token等冗余信息）
            clean_content = self._clean_content_for_ai(api_response)
            
            # 打印给AI的清理后数据
            print(f"🤖 [XHS包装器] 给AI的清理后数据:")
            print("=" * 80)
            print(clean_content)
            print("=" * 80)
            
            # 在原始结果中添加保存信息
            enhanced_result = MCPToolResult(
                content=clean_content,  # 使用清理后的内容给AI
                metadata={
                    **getattr(original_result, 'metadata', {}),
                    'data_saved': True,
                    'saved_info': saved_data,
                    'tool_name': tool_name,
                    'save_timestamp': datetime.now().isoformat(),
                    'content_cleaned': True
                }
            )
            
            print(f"✅ [XHS包装器] 小红书工具 {tool_name} 数据保存完成: {saved_data}")
            print(f"✅ 小红书工具 {tool_name} 数据保存完成: {saved_data}")
            return enhanced_result
            
        except Exception as e:
            print(f"❌ [XHS包装器] 处理小红书工具调用失败: {e}")
            print(f"❌ [XHS包装器] 错误类型: {type(e).__name__}")
            import traceback
            print(f"❌ [XHS包装器] 错误堆栈: {traceback.format_exc()}")
            logger.error(f"❌ 处理小红书工具调用失败: {e}")
            
            # 记录错误日志
            response_time = time.time() - start_time
            print(f"📊 [XHS包装器] 记录错误日志...")
            try:
                cleaned_tool_args = self._clean_tool_args(tool_args)
                await self.xhs_service.save_api_log(
                    api_name=tool_name,
                    request_params=cleaned_tool_args,  # 使用清理后的参数
                    response_data={},
                    response_time=response_time,
                    success=False,
                    error_message=str(e)
                )
                print(f"📊 [XHS包装器] 错误日志记录成功")
            except Exception as log_error:
                print(f"📊 [XHS包装器] 错误日志记录失败: {log_error}")
            
            # 返回原始结果，但添加错误信息
            return MCPToolResult(
                content=original_result.content,
                metadata={
                    **getattr(original_result, 'metadata', {}),
                    'data_saved': False,
                    'save_error': str(e),
                    'tool_name': tool_name,
                    'save_timestamp': datetime.now().isoformat()
                }
            )
    
    async def _save_tool_data(self, tool_name: str, tool_args: Dict[str, Any], 
                            api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据工具类型保存数据
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数（已清理）
            api_response: API响应数据
            
        Returns:
            保存结果信息
        """
        save_info = {"tool_name": tool_name, "saved_items": []}
        
        print(f"🏗️ [XHS数据保存] 开始处理工具: {tool_name}")
        print(f"🏗️ [XHS数据保存] 工具参数: {tool_args}")
        
        try:
            if tool_name == 'home_feed':
                print(f"🏠 [XHS数据保存] 处理首页推荐笔记...")
                # 保存首页推荐笔记
                save_result = await self.xhs_service.save_note_data(
                    api_response, 
                    source="home_feed"
                )
                print(f"🏠 [XHS数据保存] 首页推荐笔记保存完成，结果: {save_result}")
                save_info["saved_items"] = save_result.get("note_ids", [])
                save_info["count"] = save_result.get("saved_count", 0)
                save_info["type"] = "notes"
                
            elif tool_name == 'search_notes':
                print(f"🔍 [XHS数据保存] 处理搜索笔记结果...")
                # 保存搜索笔记结果
                keywords = tool_args.get('keywords', '')
                print(f"🔍 [XHS数据保存] 搜索关键词: {keywords}")
                
                save_result = await self.xhs_service.save_note_data(
                    api_response, 
                    source="search", 
                    search_keyword=keywords
                )
                print(f"🔍 [XHS数据保存] 搜索笔记保存完成，结果: {save_result}")
                
                # 保存搜索记录
                result_count = save_result.get("saved_count", 0)
                has_more = api_response.get('data', {}).get('has_more', False)
                print(f"🔍 [XHS数据保存] 准备保存搜索记录: 结果数量={result_count}, 是否还有更多={has_more}")
                
                search_record_id = await self.xhs_service.save_search_record(
                    keyword=keywords,
                    result_count=result_count,
                    has_more=has_more
                )
                print(f"🔍 [XHS数据保存] 搜索记录保存完成，ID: {search_record_id}")
                
                save_info["saved_items"] = save_result.get("note_ids", [])
                save_info["count"] = save_result.get("saved_count", 0)
                save_info["type"] = "notes"
                save_info["search_record_id"] = search_record_id
                save_info["keywords"] = keywords
                
            elif tool_name == 'get_note_content':
                # 保存笔记详细内容
                save_result = await self.xhs_service.save_note_data(
                    api_response, 
                    source="api"
                )
                save_info["saved_items"] = save_result.get("note_ids", [])
                save_info["count"] = save_result.get("saved_count", 0)
                save_info["type"] = "note_detail"
                
            elif tool_name in ['get_note_comments', 'post_comment']:
                # 评论功能已移除
                save_info["type"] = "comments_disabled"
                save_info["message"] = "评论功能已移除"
                
            else:
                save_info["error"] = f"未知的小红书工具: {tool_name}"
                
        except Exception as e:
            print(f"❌ [XHS数据保存] 保存 {tool_name} 数据失败: {e}")
            print(f"❌ [XHS数据保存] 错误类型: {type(e).__name__}")
            import traceback
            print(f"❌ [XHS数据保存] 错误堆栈: {traceback.format_exc()}")
            logger.error(f"保存 {tool_name} 数据失败: {e}")
            save_info["error"] = str(e)
        
        return save_info
    
    def _clean_content_for_ai(self, api_response: Dict[str, Any]) -> str:
        """
        为AI清理内容，移除URL、token等冗余信息，只保留有用的分析信息
        
        Args:
            api_response: 原始API响应
            
        Returns:
            清理后的内容字符串
        """
        try:
            import json
            
            # 需要移除的字段（URL、token等）
            url_fields = [
                'url', 'avatar', 'image', 'cover', 'url_default', 'url_pre', 
                'xsec_token', 'token', 'link', 'href', 'src'
            ]
            
            def clean_dict(obj):
                """递归清理字典中的URL和token字段"""
                if isinstance(obj, dict):
                    cleaned = {}
                    for key, value in obj.items():
                        # 跳过URL相关字段
                        if any(field in key.lower() for field in url_fields):
                            continue
                        # 跳过info_list（包含图片URL）
                        if key == 'info_list':
                            continue
                        # 递归处理嵌套对象
                        cleaned[key] = clean_dict(value)
                    return cleaned
                elif isinstance(obj, list):
                    return [clean_dict(item) for item in obj]
                else:
                    return obj
            
            # 清理API响应
            cleaned_response = clean_dict(api_response)
            
            # 如果有笔记数据，提取关键信息用于AI分析
            if 'data' in cleaned_response and 'items' in cleaned_response['data']:
                items = cleaned_response['data']['items']
                ai_friendly_data = {
                    'success': cleaned_response.get('success', True),
                    'total_items': len(items),
                    'notes': []
                }
                
                for item in items[:10]:  # 限制给AI的笔记数量
                    if 'note_card' in item:
                        note_card = item['note_card']
                        note_info = {
                            'id': item.get('id', ''),
                            'title': note_card.get('display_title', ''),
                            'type': note_card.get('type', ''),
                            'user': {
                                'nickname': note_card.get('user', {}).get('nickname', ''),
                                'user_id': note_card.get('user', {}).get('user_id', '')
                            },
                            'interactions': {
                                'liked_count': note_card.get('interact_info', {}).get('liked_count', 0),
                                'comment_count': note_card.get('interact_info', {}).get('comment_count', 0),
                                'collected_count': note_card.get('interact_info', {}).get('collected_count', 0),
                                'shared_count': note_card.get('interact_info', {}).get('shared_count', 0)
                            },
                            'publish_time': next(
                                (tag.get('text', '') for tag in note_card.get('corner_tag_info', [])
                                 if isinstance(tag, dict) and tag.get('type') == 'publish_time'), 
                                ''
                            ),
                            'image_count': len(note_card.get('image_list', [])),
                        }
                        ai_friendly_data['notes'].append(note_info)
                
                return json.dumps(ai_friendly_data, ensure_ascii=False, indent=2)
            else:
                # 对于其他类型的响应，返回清理后的数据
                return json.dumps(cleaned_response, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ [XHS包装器] 清理AI内容失败: {e}")
            # 如果清理失败，返回基本信息
            return json.dumps({
                'success': api_response.get('success', False),
                'message': '数据已保存到数据库，请通过数据管理页面查看详细信息',
                'code': api_response.get('code', 0)
            }, ensure_ascii=False)
    
    def _extract_note_id_from_url(self, url: str) -> Optional[str]:
        """从URL中提取笔记ID"""
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            return parsed_url.path.split('/')[-1]
        except Exception:
            return None
    
    async def get_saved_data_summary(self, tool_name: str, time_range: str = "today") -> Dict[str, Any]:
        """
        获取保存数据的摘要信息
        
        Args:
            tool_name: 工具名称
            time_range: 时间范围 (today, week, month)
            
        Returns:
            数据摘要
        """
        try:
            if time_range == "today":
                # 获取今日统计
                stats = await self.xhs_service.get_statistics()
                return {
                    "tool_name": tool_name,
                    "time_range": time_range,
                    "statistics": stats
                }
            else:
                # 其他时间范围的统计可以后续扩展
                return {
                    "tool_name": tool_name,
                    "time_range": time_range,
                    "message": "暂不支持此时间范围"
                }
                
        except Exception as e:
            logger.error(f"获取数据摘要失败: {e}")
            return {
                "tool_name": tool_name,
                "time_range": time_range,
                "error": str(e)
            }


# 创建全局实例
xhs_mcp_wrapper = XhsMCPWrapperService() 