#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书API接口测试Demo
用于验证各个接口的返回数据格式
"""

import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.xhs_api import XhsApi
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 小红书cookie（从main.py中复制）
XHS_COOKIE = "gid=yYdKy2f2q2uSyYdKy2fKjT1d2iIkdiKl9T9kx2U1JhiE742817DJUE888J4WWqY8jqfYjqf2; x-user-id-ark.xiaohongshu.com=5cfb51d100000000170277d9; customerClientId=237676388163235; x-user-id-school.xiaohongshu.com=5cfb51d100000000170277d9; x-user-id-idea.xiaohongshu.com=5cfb51d100000000170277d9; x-user-id-xue.xiaohongshu.com=5cfb51d100000000170277d9; abRequestId=8b2fd6af-69dd-57d8-9731-4637e41e84b0; a1=195b92bbbfcn65sdsm8kxonnlj7rn4wu0qmv04kk950000939546; webId=b01a306eb477ce6e210befde742ec7f8; x-user-id-creator.xiaohongshu.com=5cfb51d100000000170277d9; access-token-creator.xiaohongshu.com=customer.creator.AT-68c5175193758673743759541pslv2v9xhjz8vmu; galaxy_creator_session_id=sWklb9wEQ2b90Fd6sGYSei2Q0Y4skupvLjUD; galaxy.creator.beaker.session.id=1750741123609076061264; access-token-xue.xiaohongshu.com=customer.xue.AT-68c517521217862883296034jroblrpdf6cppeyf; sensorsdata2015jssdkcross=%7B%22%24device_id%22%3A%22197b9dffeb1a38-0e2c26f54cf636-26011e51-2359296-197b9dffeb22869%22%7D; xsecappid=xhs-pc-web; webBuild=4.72.0; acw_tc=0ad581fa17520539198778256e89383cc0988dda5f130a69b85180d00561c9; web_session=040069b634e26324ab49ea735b3a4bf67225ad; unread={%22ub%22:%22686507c40000000020019a4c%22%2C%22ue%22:%22686bb0b500000000120309be%22%2C%22uc%22:23}; websectiga=6169c1e84f393779a5f7de7303038f3b47a78e47be716e7bec57ccce17d45f99; sec_poison_id=c3aff0ac-410c-47a5-8bc1-a56f5bc23385; loadts=1752054856737"


class XhsApiTester:
    def __init__(self):
        self.api = XhsApi(cookie=XHS_COOKIE)
        
    def save_json_to_file(self, data, filename):
        """保存JSON数据到文件"""
        os.makedirs("test_results", exist_ok=True)
        filepath = f"test_results/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存到: {filepath}")
        
    async def test_home_feed(self):
        """测试首页推荐接口"""
        logger.info("=== 测试首页推荐接口 ===")
        try:
            # 测试带评论的请求
            logger.info("获取首页推荐（包含评论）...")
            data = await self.api.home_feed(fetch_content=True, fetch_comments=True)
            self.save_json_to_file(data, "home_feed_response.json")
            
            # 验证数据结构
            if 'data' in data and 'items' in data['data']:
                items = data['data']['items']
                logger.info(f"获取到 {len(items)} 条笔记")
                
                # 统计包含评论的笔记数
                comments_count = sum(1 for item in items if 'comments' in item and item['comments'])
                logger.info(f"包含评论的笔记数: {comments_count}/{len(items)}")
                
                # 分析第一条笔记
                if items:
                    first_note = items[0]
                    logger.info(f"\n笔记数据示例 (ID: {first_note.get('id', 'unknown')}):")
                    logger.info(f"- 标题: {first_note.get('display_title', '无标题')}")
                    logger.info(f"- 笔记URL: {first_note.get('note_url', '无URL')}")
                    
                    # 检查图片格式
                    if 'images' in first_note:
                        logger.info(f"- 图片数量: {len(first_note['images'])}")
                        if first_note['images']:
                            logger.info(f"- 图片列表示例: {first_note['images'][:2]}")
                            
                    # 检查评论
                    if 'comments' in first_note and first_note['comments']:
                        logger.info(f"- 评论数量: {len(first_note['comments'])}")
                        if first_note['comments']:
                            first_comment = first_note['comments'][0]
                            logger.info(f"- 第一条评论内容: {first_comment.get('content', '无内容')}")
                            logger.info(f"- 点赞数: {first_comment.get('like_count', 0)}")
                            logger.info(f"- 是否有子评论: {first_comment.get('sub_comment_has_more', False)}")
            
            return data
        except Exception as e:
            logger.error(f"首页推荐接口测试失败: {e}", exc_info=True)
            return None
            
    async def test_search_notes(self, keywords="美食"):
        """测试搜索笔记接口"""
        logger.info(f"=== 测试搜索笔记接口: {keywords} ===")
        try:
            # 测试带评论的请求
            logger.info(f"搜索笔记: {keywords}")
            data = await self.api.search_notes(keywords, fetch_content=True, fetch_comments=True)
            self.save_json_to_file(data, f"search_notes_{keywords}_response.json")
            
            # 验证数据结构
            if 'data' in data and 'items' in data['data']:
                items = data['data']['items']
                logger.info(f"搜索到 {len(items)} 条笔记")
                
                # 统计
                comments_count = sum(1 for item in items if 'comments' in item and item['comments'])
                comments_total = sum(len(item.get('comments', [])) for item in items)
                
                logger.info(f"\n数据统计:")
                logger.info(f"- 包含评论的笔记数: {comments_count}/{len(items)}")
                logger.info(f"- 总评论数: {comments_total}")
                
                # 分析第一条笔记
                if items:
                    first_note = items[0]
                    logger.info(f"\n笔记数据示例 (ID: {first_note.get('id', 'unknown')}):")
                    logger.info(f"- 标题: {first_note.get('display_title', '无标题')}")
                    logger.info(f"- 发布时间: {first_note.get('time', '无时间')}")
                    
                    # 检查图片格式
                    if 'images' in first_note:
                        logger.info(f"- 图片数量: {len(first_note['images'])}")
                        if first_note['images']:
                            logger.info(f"- 图片列表示例: {first_note['images'][:2]}")
                    
                    # 检查评论
                    if 'comments' in first_note and first_note['comments']:
                        logger.info(f"- 评论数量: {len(first_note['comments'])}")
                        if first_note['comments']:
                            first_comment = first_note['comments'][0]
                            logger.info(f"- 第一条评论内容: {first_comment.get('content', '无内容')}")
            
            return data
        except Exception as e:
            logger.error(f"搜索笔记接口测试失败: {e}", exc_info=True)
            return None
            
    async def test_get_note_content(self, note_id=None, xsec_token=None):
        """测试获取笔记内容接口"""
        logger.info("=== 测试获取笔记内容接口 ===")
        
        # 如果没有提供参数，先从首页获取一个
        if not note_id or not xsec_token:
            home_data = await self.test_home_feed()
            if home_data and 'data' in home_data and 'items' in home_data['data']:
                first_note = home_data['data']['items'][0]
                note_id = first_note['id']
                xsec_token = first_note['xsec_token']
                logger.info(f"使用首页第一条笔记进行测试: note_id={note_id}, xsec_token={xsec_token[:20]}...")
        
        if not note_id or not xsec_token:
            logger.error("无法获取测试用的笔记ID和token")
            return None
            
        try:
            logger.info(f"note_id: {note_id}, xsec_token: {xsec_token[:20]}...")
            
            data = await self.api.get_note_content(note_id, xsec_token)
            self.save_json_to_file(data, f"note_content_{note_id}_response.json")
            
            # 分析笔记内容
            if 'data' in data and 'items' in data['data'] and data['data']['items']:
                note = data['data']['items'][0]
                if 'note_card' in note:
                    note_card = note['note_card']
                    logger.info("笔记详细信息:")
                    logger.info(f"- 标题: {note_card.get('title')}")
                    logger.info(f"- 内容: {note_card.get('desc', '')[:100]}...")
                    logger.info(f"- 发布时间: {note_card.get('time')}")
                    
                    if 'image_list' in note_card:
                        logger.info(f"- 图片数量: {len(note_card['image_list'])}")
                        
            return data
        except Exception as e:
            logger.error(f"获取笔记内容接口测试失败: {e}")
            return None
            
    async def test_get_note_comments(self, note_id=None, xsec_token=None):
        """测试获取笔记评论接口"""
        logger.info("=== 测试获取笔记评论接口 ===")
        
        # 如果没有提供参数，先从首页获取一个
        if not note_id or not xsec_token:
            home_data = await self.test_home_feed()
            if home_data and 'data' in home_data and 'items' in home_data['data']:
                first_note = home_data['data']['items'][0]
                note_id = first_note['id']
                xsec_token = first_note['xsec_token']
                logger.info(f"使用首页第一条笔记进行测试: note_id={note_id}, xsec_token={xsec_token[:20]}...")
        
        if not note_id or not xsec_token:
            logger.error("无法获取测试用的笔记ID和token")
            return None
            
        try:
            data = await self.api.get_note_comments(note_id, xsec_token)
            self.save_json_to_file(data, f"note_comments_{note_id}_response.json")
            
            # 分析评论数据
            if 'data' in data and 'comments' in data['data']:
                comments = data['data']['comments']
                logger.info(f"获取到 {len(comments)} 条评论")
                
                # 分析前几条评论
                for i, comment in enumerate(comments[:3]):
                    logger.info(f"评论{i+1}: {comment['user_info']['nickname']}: {comment['content'][:50]}...")
                    
            return data
        except Exception as e:
            logger.error(f"获取笔记评论接口测试失败: {e}")
            return None
            
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行小红书API接口测试...")
        
        # 1. 测试首页推荐
        await self.test_home_feed()
        
        # 添加延时，避免请求过于频繁
        logger.info("等待10秒后继续测试...")
        await asyncio.sleep(10)
        
        # 2. 测试搜索功能 - 只测试一个关键词
        await self.test_search_notes("美食")
        
        logger.info("所有测试完成!")


async def main():
    """主函数"""
    tester = XhsApiTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 