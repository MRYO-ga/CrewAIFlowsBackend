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
                print(f"🗄️ [XhsService] 处理第 {i} 个笔记项目")
                
                # 创建新的数据库会话，避免会话回滚问题
                db = SessionLocal()
                note_id = "unknown"  # 初始化note_id，避免引用错误
                
                try:
                    # 检查数据类型和结构
                    if not isinstance(note_item, dict):
                        print(f"❌ [XhsService] 笔记项目不是字典类型，跳过")
                        continue
                    
                    print(f"🔍 [XhsService] 笔记项目键: {list(note_item.keys())}")
                    
                    # 获取笔记ID
                    note_id = note_item.get('id', '')
                    if not note_id:
                        print("⚠️ [XhsService] 笔记ID为空，跳过")
                        continue
                    
                    print(f"🗄️ [XhsService] 笔记ID: {note_id}")
                    
                    # 检查笔记是否已存在
                    existing_note = db.query(XhsNote).filter(XhsNote.id == note_id).first()
                    if existing_note:
                        print(f"🔄 [XhsService] 笔记 {note_id} 已存在，跳过")
                        saved_note_ids.append(note_id)
                        continue
                    
                    # 获取note_card数据
                    note_card = note_item.get('note_card', {})
                    if not isinstance(note_card, dict):
                        print(f"⚠️ [XhsService] note_card字段缺失或格式错误，跳过")
                        continue
                    
                    print(f"🔍 [XhsService] note_card键: {list(note_card.keys())}")
                    
                    # 获取笔记标题
                    display_title = note_card.get('display_title', '')
                    title = note_card.get('title', display_title)
                    desc = note_card.get('desc', '')
                    print(f"🗄️ [XhsService] 笔记标题: {display_title}")
                    print(f"🗄️ [XhsService] 笔记内容: {desc[:100]}...")
                    
                    # 创建新笔记记录
                    note = XhsNote(
                        id=note_id,
                        display_title=display_title[:500] if display_title else '',  # 限制长度
                        title=title[:500] if title else '',  # 限制长度
                        desc=desc[:5000] if desc else '',  # 限制描述长度
                        content=str(note_card.get('content', ''))[:5000],  # 限制内容长度
                        note_type=str(note_card.get('type', 'normal')),
                        model_type=str(note_item.get('model_type', 'note')),
                        source=source,
                        search_keyword=search_keyword
                    )
                    
                    # 用户信息 - 从note_card.user中获取
                    user_info = note_card.get('user', {})
                    if isinstance(user_info, dict):
                        note.user_id = str(user_info.get('user_id', ''))
                        note.user_nickname = str(user_info.get('nickname', user_info.get('nick_name', '')))[:200]  # 限制长度
                        note.user_avatar = str(user_info.get('avatar', ''))[:500]  # 限制长度
                        print(f"🗄️ [XhsService] 用户信息: {note.user_nickname} ({note.user_id})")
                    
                    # 互动数据 - 从note_card.interact_info中获取
                    interact_info = note_card.get('interact_info', {})
                    if isinstance(interact_info, dict):
                        # 确保数值类型正确转换，处理字符串数字
                        try:
                            note.liked_count = int(str(interact_info.get('liked_count', 0)).replace(',', ''))
                        except (ValueError, TypeError):
                            note.liked_count = 0
                        
                        try:
                            note.comment_count = int(str(interact_info.get('comment_count', 0)).replace(',', ''))
                        except (ValueError, TypeError):
                            note.comment_count = 0
                        
                        try:
                            note.collected_count = int(str(interact_info.get('collected_count', 0)).replace(',', ''))
                        except (ValueError, TypeError):
                            note.collected_count = 0
                        
                        try:
                            note.shared_count = int(str(interact_info.get('shared_count', 0)).replace(',', ''))
                        except (ValueError, TypeError):
                            note.shared_count = 0
                        
                        note.liked = bool(interact_info.get('liked', False))
                        note.collected = bool(interact_info.get('collected', False))
                        
                        print(f"🗄️ [XhsService] 互动数据: 点赞{note.liked_count} 评论{note.comment_count} 收藏{note.collected_count}")
                    
                    # 封面图片信息 - 从note_card.cover中获取
                    cover_info = note_card.get('cover', {})
                    if isinstance(cover_info, dict):
                        note.cover_url_default = str(cover_info.get('url_default', ''))[:500]
                        note.cover_url_pre = str(cover_info.get('url_pre', ''))[:500]
                        
                        # 确保数值类型正确转换
                        try:
                            note.cover_height = int(cover_info.get('height', 0))
                        except (ValueError, TypeError):
                            note.cover_height = 0
                        
                        try:
                            note.cover_width = int(cover_info.get('width', 0))
                        except (ValueError, TypeError):
                            note.cover_width = 0
                        
                        print(f"🗄️ [XhsService] 封面信息: {note.cover_width}x{note.cover_height}")
                    
                    # 图片列表 - 从note_card.image_list中获取，确保是JSON可序列化的
                    image_list = note_card.get('image_list', [])
                    if image_list and isinstance(image_list, (list, dict)):
                        try:
                            # 测试JSON序列化能力，但不改变数据类型
                            json_str = json.dumps(image_list, ensure_ascii=False)
                            if len(json_str) < 10000:  # 限制JSON大小
                                # SQLAlchemy的JSON字段接受Python对象
                                note.image_list = image_list
                                print(f"🗄️ [XhsService] 图片列表: {len(image_list) if isinstance(image_list, list) else 1}张")
                            else:
                                print("⚠️ [XhsService] 图片列表JSON过大，设为空列表")
                                note.image_list = []
                        except (TypeError, ValueError, UnicodeDecodeError) as e:
                            print(f"⚠️ [XhsService] 图片列表JSON序列化失败: {e}")
                            note.image_list = []
                    else:
                        note.image_list = []
                    
                    # 角标信息 - 从note_card.corner_tag_info中获取，确保是JSON可序列化的
                    corner_tag_info = note_card.get('corner_tag_info', [])
                    if corner_tag_info and isinstance(corner_tag_info, (list, dict)):
                        try:
                            # 测试JSON序列化能力，但不改变数据类型
                            json_str = json.dumps(corner_tag_info, ensure_ascii=False)
                            if len(json_str) < 5000:  # 限制JSON大小
                                # SQLAlchemy的JSON字段接受Python对象
                                note.corner_tag_info = corner_tag_info
                                # 尝试从角标信息中提取发布时间
                                if isinstance(corner_tag_info, list):
                                    for tag in corner_tag_info:
                                        if isinstance(tag, dict) and tag.get('type') == 'publish_time':
                                            publish_time_text = tag.get('text', '')
                                            print(f"🗄️ [XhsService] 发布时间文本: {publish_time_text}")
                                            break
                            else:
                                print("⚠️ [XhsService] 角标信息JSON过大，设为空列表")
                                note.corner_tag_info = []
                        except (TypeError, ValueError, UnicodeDecodeError) as e:
                            print(f"⚠️ [XhsService] 角标信息JSON序列化失败: {e}")
                            note.corner_tag_info = []
                    else:
                        note.corner_tag_info = []
                    
                    # 发布时间 - 尝试从多个字段获取
                    try:
                        publish_time = note_item.get('time', note_card.get('time', 0))
                        if isinstance(publish_time, str):
                            publish_time = int(publish_time) if publish_time.isdigit() else 0
                        note.publish_time = int(publish_time)
                    except (ValueError, TypeError):
                        note.publish_time = 0
                    
                    # 添加到数据库
                    db.add(note)
                    db.commit()
                    saved_note_ids.append(note_id)
                    print(f"✅ [XhsService] 笔记 {note_id} 保存成功")
                    
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
                    'title': note.title,
                    'desc': note.desc,
                    'content': note.content[:200] + '...' if len(note.content) > 200 else note.content,
                    'user_nickname': note.user_nickname,
                    'user_avatar': note.user_avatar,
                    'liked_count': note.liked_count,
                    'comment_count': note.comment_count,
                    'collected_count': note.collected_count,
                    'shared_count': note.shared_count,
                    'cover_url_pre': note.cover_url_pre,
                    'source': note.source,
                    'search_keyword': note.search_keyword,
                    'publish_time': note.publish_time,
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
                'title': note.title,
                'desc': note.desc,
                'content': note.content,
                'note_type': note.note_type,
                'user_id': note.user_id,
                'user_nickname': note.user_nickname,
                'user_avatar': note.user_avatar,
                'liked_count': note.liked_count,
                'comment_count': note.comment_count,
                'collected_count': note.collected_count,
                'shared_count': note.shared_count,
                'cover_url_default': note.cover_url_default,
                'cover_url_pre': note.cover_url_pre,
                'image_list': note.image_list,
                'corner_tag_info': note.corner_tag_info,
                'publish_time': note.publish_time,
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
            
            # 为AI提取关键信息
            ai_notes = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                note_card = item.get('note_card', {})
                if not note_card:
                    continue
                
                # 提取用户信息
                user_info = note_card.get('user', {})
                user_data = {
                    'nickname': user_info.get('nickname', user_info.get('nick_name', '')),
                    'user_id': user_info.get('user_id', ''),
                    'xsec_token': user_info.get('xsec_token', '')  # 保留供AI调用其他接口
                }
                
                # 提取互动信息
                interact_info = note_card.get('interact_info', {})
                interaction_data = {
                    'liked_count': self._safe_int(interact_info.get('liked_count', 0)),
                    'comment_count': self._safe_int(interact_info.get('comment_count', 0)),
                    'collected_count': self._safe_int(interact_info.get('collected_count', 0)),
                    'shared_count': self._safe_int(interact_info.get('shared_count', 0)),
                    'liked': interact_info.get('liked', False),
                    'collected': interact_info.get('collected', False)
                }
                
                # 提取图片信息
                image_list = note_card.get('image_list', [])
                image_count = len(image_list) if isinstance(image_list, list) else 0
                
                # 提取标签信息
                tag_list = note_card.get('tag_list', [])
                tags = [tag.get('name', '') for tag in tag_list if isinstance(tag, dict) and tag.get('name')]
                
                # 提取发布时间
                corner_tag_info = note_card.get('corner_tag_info', [])
                publish_time = ''
                for tag in corner_tag_info:
                    if isinstance(tag, dict) and tag.get('type') == 'publish_time':
                        publish_time = tag.get('text', '')
                        break
                
                # 构建AI友好的笔记信息
                note_info = {
                    'id': item.get('id', ''),
                    'title': note_card.get('title', note_card.get('display_title', '')),
                    'desc': note_card.get('desc', ''),
                    'type': note_card.get('type', ''),
                    'model_type': item.get('model_type', ''),
                    'user': user_data,
                    'interactions': interaction_data,
                    'image_count': image_count,
                    'tags': tags,
                    'publish_time': publish_time,
                    'time': item.get('time', 0),
                    'ip_location': note_card.get('ip_location', ''),
                    'saved_to_db': item.get('id', '') in saved_note_ids
                }
                
                ai_notes.append(note_info)
            
            # 构建AI友好的数据结构
            ai_data = {
                'success': True,
                'total_items': len(items),
                'saved_count': saved_count,
                'current_time': response_data.get('current_time', 0),
                'cursor_score': response_data.get('cursor_score', ''),
                'has_more': response_data.get('has_more', False),
                'notes': ai_notes,
                'data_source': source,
                'search_keyword': search_keyword,
                'processing_time': datetime.now().isoformat()
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