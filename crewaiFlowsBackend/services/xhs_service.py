#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书服务类
用于处理小红书数据的数据库操作和数据转换
"""

import json
import uuid
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from database.database import get_db, SessionLocal
from database.models import XhsNote, XhsSearchRecord, XhsApiLog
from utils.intelligent_data_service import IntelligentDataService
import logging

logger = logging.getLogger(__name__)


class XhsService:
    """小红书服务类"""
    
    def __init__(self):
        self.data_service = IntelligentDataService()
    
    def generate_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4()).replace('-', '')
    
    async def save_note_data(self, data: Dict[str, Any], source: str = "api", search_keyword: str = None) -> Dict[str, Any]:
        """保存笔记数据到数据库"""
        print(f"🗄️ [XhsService] 开始保存笔记数据，来源: {source}")
        
        try:
            # 解析数据
            if isinstance(data, str):
                data = json.loads(data)
            
            print(f"🔍 [XhsService] 解析后数据类型: {type(data)}")
            print(f"🔍 [XhsService] 解析后数据键: {list(data.keys()) if isinstance(data, dict) else '非字典类型'}")
            
            # 根据提供的格式，数据结构应该是: data -> data -> items
            response_data = data.get('data', {})
            if not response_data:
                print("⚠️ [XhsService] 没有找到data字段")
                return {"saved_count": 0, "note_ids": []}
            
            notes_list = response_data.get('items', [])
            if not notes_list:
                print("⚠️ [XhsService] 没有找到items字段")
                print(f"🔍 [XhsService] response_data结构: {list(response_data.keys()) if isinstance(response_data, dict) else '非字典'}")
                return {"saved_count": 0, "note_ids": []}
            
            print(f"🗄️ [XhsService] 找到 {len(notes_list)} 个笔记项目")
            
            if not isinstance(notes_list, list):
                print(f"❌ [XhsService] items不是列表类型: {type(notes_list)}")
                return {"saved_count": 0, "note_ids": []}
            
            saved_note_ids = []
            
            for i, note_item in enumerate(notes_list, 1):
                # print(f"🗄️ [XhsService] 处理第 {i} 个笔记项目")
                
                # 创建新的数据库会话，避免会话回滚问题
                db = SessionLocal()
                note_id = "unknown"  # 初始化note_id，避免引用错误
                
                try:
                    # 检查数据类型和结构
                    if not isinstance(note_item, dict):
                        print(f"❌ [XhsService] 笔记项目不是字典类型，跳过")
                        continue
                    
                    # print(f"🔍 [XhsService] 笔记项目键: {list(note_item.keys())}")
                    
                    # 获取笔记ID
                    note_id = note_item.get('id', '')
                    if not note_id:
                        print("⚠️ [XhsService] 笔记ID为空，跳过")
                        continue
                    
                    # print(f"🗄️ [XhsService] 笔记ID: {note_id}")
                    
                    # 检查笔记是否已存在
                    existing_note = db.query(XhsNote).filter(XhsNote.id == note_id).first()
                    if existing_note:
                        # print(f"🔄 [XhsService] 笔记 {note_id} 已存在，跳过")
                        saved_note_ids.append(note_id)
                        continue
                    
                    # 创建新笔记记录
                    note = XhsNote(
                        id=note_id,
                        model_type=str(note_item.get('model_type', 'note')),
                        xsec_token=str(note_item.get('xsec_token', '')),
                        note_url=str(note_item.get('note_url', '')),
                        
                        # 笔记基本信息
                        type=str(note_item.get('type', 'normal')),
                        display_title=note_item.get('display_title', '')[:500] if note_item.get('display_title') else '',
                        desc=note_item.get('desc', '')[:5000] if note_item.get('desc') else '',
                        ip_location=str(note_item.get('ip_location', '')),
                        
                        # 时间信息
                        time=str(note_item.get('time', '')),
                        timestamp=note_item.get('timestamp', 0),
                        last_update_time=str(note_item.get('last_update_time', '')),
                        
                        # 数据来源
                        source=source,
                        search_keyword=search_keyword
                    )
                    
                    # 用户信息
                    user_info = note_item.get('user', {})
                    if isinstance(user_info, dict):
                        note.user_id = str(user_info.get('user_id', ''))
                        note.user_nickname = str(user_info.get('nickname', ''))[:200]  # 限制长度
                        note.user_avatar = str(user_info.get('avatar', ''))[:500]  # 限制长度
                        note.user_xsec_token = str(user_info.get('xsec_token', ''))
                    
                    # 互动数据 - 直接保存为字符串
                    interact_info = note_item.get('interact_info', {})
                    if isinstance(interact_info, dict):
                        note.liked_count = str(interact_info.get('liked_count', '0'))
                        note.comment_count = str(interact_info.get('comment_count', '0'))
                        note.collected_count = str(interact_info.get('collected_count', '0'))
                        note.share_count = str(interact_info.get('share_count', '0'))
                    
                    # 封面图片信息
                    note.cover_image = str(note_item.get('cover_image', ''))[:500]
                    
                    # 图片列表
                    images = note_item.get('images', [])
                    if images and isinstance(images, list):
                        try:
                            # 直接保存URL列表
                            json_str = json.dumps(images, ensure_ascii=False)
                            if len(json_str) < 10000:  # 限制JSON大小
                                note.images = images
                            else:
                                print("⚠️ [XhsService] 图片列表JSON过大，设为空列表")
                                note.images = []
                        except (TypeError, ValueError, UnicodeDecodeError) as e:
                            print(f"⚠️ [XhsService] 图片列表JSON序列化失败: {e}")
                            note.images = []
                    
                    # 评论数据
                    comments = note_item.get('comments', [])
                    if comments and isinstance(comments, list):
                        try:
                            json_str = json.dumps(comments, ensure_ascii=False)
                            if len(json_str) < 10000:  # 限制JSON大小
                                note.comments_json = comments
                                print(f"🗄️ [XhsService] 评论数据: {len(comments)}条")
                            else:
                                print("⚠️ [XhsService] 评论数据JSON过大，设为空列表")
                                note.comments_json = []
                        except (TypeError, ValueError, UnicodeDecodeError) as e:
                            print(f"⚠️ [XhsService] 评论数据JSON序列化失败: {e}")
                            note.comments_json = []
                    
                    # 添加到数据库
                    db.add(note)
                    db.commit()
                    saved_note_ids.append(note_id)
                    # print(f"✅ [XhsService] 笔记 {note_id} 保存成功")
                    
                except Exception as add_error:
                    print(f"❌ [XhsService] 保存笔记 {note_id} 失败: {add_error}")
                    db.rollback()
                    # 继续处理下一个笔记
                finally:
                    db.close()  # 关闭当前会话
            
            if saved_note_ids:
                print(f"✅ [XhsService] 成功保存 {len(saved_note_ids)} 个笔记记录")
            else:
                print("⚠️ [XhsService] 没有成功添加的笔记记录")
            
            logger.info(f"成功保存 {len(saved_note_ids)} 条笔记数据")
            print(f"✅ [XhsService] 数据保存完成，成功保存 {len(saved_note_ids)} 条笔记数据")
            
            return {"saved_count": len(saved_note_ids), "note_ids": saved_note_ids}
            
        except Exception as e:
            print(f"❌ [XhsService] 保存笔记数据失败: {e}")
            import traceback
            print(f"❌ [XhsService] 错误堆栈: {traceback.format_exc()}")
            logger.error(f"保存笔记数据失败: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
                
        return {"saved_count": 0, "note_ids": []}
    

    
    async def save_search_record(self, keyword: str, result_count: int, has_more: bool = False, 
                               page: int = 1, page_size: int = 20) -> str:
        """
        保存搜索记录
        
        Args:
            keyword: 搜索关键词
            result_count: 结果数量
            has_more: 是否还有更多
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索记录ID
        """
        try:
            db = next(get_db())
            
            record_id = self.generate_id()
            search_record = XhsSearchRecord(
                id=record_id,
                keyword=keyword,
                result_count=result_count,
                page=page,
                page_size=page_size,
                has_more=has_more
            )
            
            db.add(search_record)
            db.commit()
            
            logger.info(f"保存搜索记录: {keyword} - {result_count} 条结果")
            return record_id
            
        except Exception as e:
            logger.error(f"保存搜索记录失败: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
        
        return ""
    
    async def save_api_log(self, api_name: str, request_params: Dict, response_data: Dict, 
                         response_time: float, success: bool = True, error_message: str = None) -> str:
        """
        保存API调用日志
        
        Args:
            api_name: API名称
            request_params: 请求参数
            response_data: 响应数据
            response_time: 响应时间
            success: 是否成功
            error_message: 错误信息
            
        Returns:
            日志ID
        """
        try:
            db = next(get_db())
            
            log_id = self.generate_id()
            
            # 计算数据条数
            data_count = 0
            if response_data and 'data' in response_data and response_data['data']:
                if 'items' in response_data['data']:
                    data_count = len(response_data['data']['items'])
                elif 'comments' in response_data['data']:
                    data_count = len(response_data['data']['comments'])
            
            print(f"📊 [XhsService] 保存API日志: {api_name}, 成功: {success}, 数据条数: {data_count}")
            
            api_log = XhsApiLog(
                id=log_id,
                api_name=api_name,
                request_params=request_params,
                response_code=response_data.get('code', 0) if response_data else 0,
                response_time=response_time,
                success=success,
                error_message=error_message,
                data_count=data_count
            )
            
            db.add(api_log)
            db.commit()
            
            print(f"✅ [XhsService] API日志保存成功: {log_id}")
            return log_id
            
        except Exception as e:
            print(f"❌ [XhsService] 保存API日志失败: {e}")
            import traceback
            print(f"❌ [XhsService] 错误堆栈: {traceback.format_exc()}")
            logger.error(f"保存API日志失败: {e}")
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
        
        return ""
    
    async def get_notes(self, page: int = 1, page_size: int = 20, source: str = None, 
                       search_keyword: str = None, user_id: str = None) -> Dict:
        """
        获取笔记列表
        
        Args:
            page: 页码
            page_size: 每页数量
            source: 数据来源筛选
            search_keyword: 搜索关键词筛选
            user_id: 用户ID筛选
            
        Returns:
            笔记列表和统计信息
        """
        try:
            db = next(get_db())
            
            query = db.query(XhsNote)
            
            # 添加筛选条件
            if source:
                query = query.filter(XhsNote.source == source)
            if search_keyword:
                query = query.filter(XhsNote.search_keyword.like(f"%{search_keyword}%"))
            if user_id:
                query = query.filter(XhsNote.user_id == user_id)
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            notes = query.order_by(desc(XhsNote.created_at)).offset((page - 1) * page_size).limit(page_size).all()
            
            # 转换为字典格式
            note_list = []
            for note in notes:
                note_dict = {
                    'id': note.id,
                    'display_title': note.display_title,
                    'desc': note.desc,
                    'content': note.content[:200] + '...' if len(note.content) > 200 else note.content,
                    'user_nickname': note.user_nickname,
                    'user_avatar': note.user_avatar,
                    'liked_count': note.liked_count,
                    'comment_count': note.comment_count,
                    'collected_count': note.collected_count,
                    # 兼容share_count和shared_count
                    'share_count': note.share_count if hasattr(note, 'share_count') else note.shared_count,
                    'cover_url_pre': note.cover_url_pre,
                    'source': note.source,
                    'search_keyword': note.search_keyword,
                    'publish_time': note.publish_time,
                    'publish_time_text': note.publish_time_text if hasattr(note, 'publish_time_text') else None,
                    'created_at': note.created_at.isoformat() if note.created_at else None,
                }
                note_list.append(note_dict)
            
            return {
                'notes': note_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"获取笔记列表失败: {e}")
            return {'notes': [], 'total': 0, 'page': page, 'page_size': page_size, 'total_pages': 0}
        finally:
            if 'db' in locals():
                db.close()
    
    async def get_note_detail(self, note_id: str) -> Optional[Dict]:
        """
        获取笔记详情
        
        Args:
            note_id: 笔记ID
            
        Returns:
            笔记详情
        """
        try:
            db = next(get_db())
            
            note = db.query(XhsNote).filter(XhsNote.id == note_id).first()
            if not note:
                return None
            
            # 评论功能已移除
            
            note_detail = {
                'id': note.id,
                'display_title': note.display_title,
                'desc': note.desc,
                'content': note.content,
                'note_type': note.note_type,
                'user_id': note.user_id,
                'user_nickname': note.user_nickname,
                'user_avatar': note.user_avatar,
                'liked_count': note.liked_count,
                'comment_count': note.comment_count,
                'collected_count': note.collected_count,
                # 兼容share_count和shared_count
                'share_count': note.share_count if hasattr(note, 'share_count') else note.shared_count,
                'cover_url_default': note.cover_url_default,
                'cover_url_pre': note.cover_url_pre,
                'image_list': note.image_list,
                'corner_tag_info': note.corner_tag_info,
                'publish_time': note.publish_time,
                'publish_time_text': note.publish_time_text if hasattr(note, 'publish_time_text') else None,
                'source': note.source,
                'search_keyword': note.search_keyword,
                'created_at': note.created_at.isoformat() if note.created_at else None
            }
            
            return note_detail
            
        except Exception as e:
            logger.error(f"获取笔记详情失败: {e}")
            return None
        finally:
            if 'db' in locals():
                db.close()
    
    async def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        try:
            db = next(get_db())
            
            # 笔记统计
            total_notes = db.query(XhsNote).count()
            today_notes = db.query(XhsNote).filter(
                XhsNote.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            # 用户和评论功能已移除
            
            # API调用统计
            total_api_calls = db.query(XhsApiLog).count()
            today_api_calls = db.query(XhsApiLog).filter(
                XhsApiLog.call_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            # 按来源统计笔记
            source_stats = db.execute("""
                SELECT source, COUNT(*) as count 
                FROM xhs_notes 
                GROUP BY source
            """).fetchall()
            
            source_data = {row[0]: row[1] for row in source_stats}
            
            return {
                'notes': {
                    'total': total_notes,
                    'today': today_notes
                },
                'api_calls': {
                    'total': total_api_calls,
                    'today': today_api_calls
                },
                'source_stats': source_data
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
        finally:
            if 'db' in locals():
                db.close()
    
    async def process_note_data_response(self, api_response: Dict[str, Any], source: str = "api", 
                                       search_keyword: str = None) -> Dict[str, Any]:
        """
        通用笔记数据处理方法，支持搜索接口和笔记内容接口
        
        Args:
            api_response: API返回的笔记数据
            source: 数据来源 (api, search, home_feed)
            search_keyword: 搜索关键词（如果来源是搜索）
            
        Returns:
            处理结果，包含AI友好的数据和保存状态
        """
        print(f"🔍 [XhsService] 开始处理笔记数据响应，来源: {source}")
        
        try:
            # 解析响应数据
            if isinstance(api_response, str):
                api_response = json.loads(api_response)
            
            # 检查响应状态
            if not api_response.get('success', False):
                error_msg = api_response.get('msg', '未知错误')
                print(f"❌ [XhsService] API响应失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "ai_data": None,
                    "saved_count": 0
                }
            
            # 提取数据 - 支持不同的数据结构
            response_data = api_response.get('data', {})
            items = response_data.get('items', [])
            
            if not items:
                print("⚠️ [XhsService] 没有找到笔记数据")
                return {
                    "success": True,
                    "ai_data": {
                        "success": True,
                        "total_items": 0,
                        "notes": [],
                        "message": "没有找到笔记数据"
                    },
                    "saved_count": 0
                }
            
            print(f"🔍 [XhsService] 找到 {len(items)} 个笔记项目")
            
            # 保存到数据库
            save_result = await self.save_note_data(api_response, source=source, search_keyword=search_keyword)
            saved_count = save_result.get("saved_count", 0)
            saved_note_ids = save_result.get("note_ids", [])
            
            # 为AI提取关键信息 - 简化版本，只保留必要字段
            ai_notes = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                
                # 构建AI友好的笔记信息 - 只包含必要字段
                note_info = {
                    'id': item.get('id', ''),
                    'display_title': item.get('display_title', ''),
                    'desc': item.get('desc', ''),
                    'ip_location': item.get('ip_location', ''),
                    'time': item.get('time', ''),
                    'xsec_token': item.get('xsec_token', ''),  # 保留xsec_token以便AI可以获取更多信息
                    'saved_to_db': item.get('id', '') in saved_note_ids
                }
                
                # 用户信息 - 只保留nickname
                if 'user' in item and isinstance(item['user'], dict):
                    note_info['user'] = {
                        'nickname': item['user'].get('nickname', '')
                    }
                
                # 互动信息
                if 'interact_info' in item and isinstance(item['interact_info'], dict):
                    note_info['interact_info'] = item['interact_info']
                
                # 评论信息
                if 'comments' in item and item['comments']:
                    note_info['comments'] = item['comments']
                
                ai_notes.append(note_info)
            
            # 构建AI友好的数据结构 - 简化版本
            ai_data = {
                'success': True,
                'total_items': len(items),
                'saved_count': saved_count,
                'has_more': response_data.get('has_more', False),
                'notes': ai_notes,
                'data_source': source,
                'search_keyword': search_keyword
            }
            
            print(f"✅ [XhsService] 笔记数据处理完成")
            print(f"   - 总笔记数: {len(items)}")
            print(f"   - 保存到数据库: {saved_count}")
            print(f"   - 提供给AI: {len(ai_notes)}")
            print(f"   - 数据来源: {source}")
            if search_keyword:
                print(f"   - 搜索关键词: {search_keyword}")
            
            return {
                "success": True,
                "ai_data": ai_data,
                "saved_count": saved_count,
                "saved_note_ids": saved_note_ids
            }
            
        except Exception as e:
            print(f"❌ [XhsService] 处理笔记数据响应失败: {e}")
            import traceback
            print(f"❌ [XhsService] 错误堆栈: {traceback.format_exc()}")
            logger.error(f"处理笔记数据响应失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "ai_data": None,
                "saved_count": 0
            }

    async def process_note_content_response(self, api_response: Dict[str, Any], source: str = "api") -> Dict[str, Any]:
        """
        处理笔记内容的返回接口（保持向后兼容）
        
        Args:
            api_response: API返回的笔记内容数据
            source: 数据来源
            
        Returns:
            处理结果，包含AI友好的数据和保存状态
        """
        return await self.process_note_data_response(api_response, source=source)

    def _safe_int(self, value) -> int:
        """安全转换为整数"""
        try:
            if isinstance(value, str):
                # 移除逗号等分隔符
                value = value.replace(',', '').replace('，', '')
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0 