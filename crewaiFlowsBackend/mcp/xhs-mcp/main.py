from typing import Any, List, Dict, Optional
import asyncio
import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP, Context

import requests
from api.xhs_api import XhsApi
import logging
# urllib.parse imports removed as URL parsing is no longer needed
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()

parser.add_argument("--type", type=str, default='stdio')
parser.add_argument("--port", type=int, default=8809)

args = parser.parse_args()

mcp = FastMCP("小红书", port=args.port)

# 直接硬编码cookie
xhs_cookie = "gid=yYdKy2f2q2uSyYdKy2fKjT1d2iIkdiKl9T9kx2U1JhiE742817DJUE888J4WWqY8jqfYjqf2; x-user-id-ark.xiaohongshu.com=5cfb51d100000000170277d9; customerClientId=237676388163235; x-user-id-school.xiaohongshu.com=5cfb51d100000000170277d9; x-user-id-idea.xiaohongshu.com=5cfb51d100000000170277d9; x-user-id-xue.xiaohongshu.com=5cfb51d100000000170277d9; abRequestId=8b2fd6af-69dd-57d8-9731-4637e41e84b0; a1=195b92bbbfcn65sdsm8kxonnlj7rn4wu0qmv04kk950000939546; webId=b01a306eb477ce6e210befde742ec7f8; x-user-id-creator.xiaohongshu.com=5cfb51d100000000170277d9; access-token-creator.xiaohongshu.com=customer.creator.AT-68c5175193758673743759541pslv2v9xhjz8vmu; galaxy_creator_session_id=sWklb9wEQ2b90Fd6sGYSei2Q0Y4skupvLjUD; galaxy.creator.beaker.session.id=1750741123609076061264; access-token-xue.xiaohongshu.com=customer.xue.AT-68c517521217862883296034jroblrpdf6cppeyf; sensorsdata2015jssdkcross=%7B%22%24device_id%22%3A%22197b9dffeb1a38-0e2c26f54cf636-26011e51-2359296-197b9dffeb22869%22%7D; webBuild=4.72.0; xsecappid=xhs-pc-web; web_session=040069b634e26324ab499f62423a4bafc5efdd; unread={%22ub%22:%226876375d000000001d00e072%22%2C%22ue%22:%2268776b8500000000220338a1%22%2C%22uc%22:25}; acw_tc=0ad58c4f17527417609198854e51ed8c8a3afa84790b1f2235a13c55866111; websectiga=634d3ad75ffb42a2ade2c5e1705a73c845837578aeb31ba0e442d75c648da36a; sec_poison_id=589ac0e2-b96f-4e33-899d-29e19a62a21b; loadts=1752742176748"
xhs_api = XhsApi(cookie=xhs_cookie)


# URL解析函数已移除，现在直接使用note_id和xsec_token参数


# @mcp.tool()
# async def check_cookie() -> str:
#     """检测cookie是否失效

#     """
#     try:
#         data = await xhs_api.get_me()

#         if 'success' in data and data['success'] == True:
#             return "cookie有效"
#         else:
#             return "cookie已失效"
#     except Exception as e:
#         logger.error(e)
#         return "cookie已失效"



@mcp.tool()
async def home_feed(fetch_content: bool = True, fetch_comments: bool = False) -> str:
    """获取小红书首页推荐笔记
    
    返回简化后的笔记数据，包含ID、标题、描述、用户信息、互动数据、图片URL列表等。
    如果指定fetch_comments=True，还会包含简化后的评论数据。

    Args:
        fetch_content: 是否同时获取笔记详细内容，默认为True
        fetch_comments: 是否同时获取笔记评论，默认为False
    """
    try:
        data = await xhs_api.home_feed(fetch_content=fetch_content, fetch_comments=fetch_comments)
        # logger.info(f'home_feed response: {data}')
        
        # 直接返回JSON格式的原始数据
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f'home_feed error: {e}')
        error_response = {
            "success": False,
            "error": str(e),
            "data": None
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)

@mcp.tool()
async def search_notes(keywords: str, fetch_content: bool = True, fetch_comments: bool = False) -> str:
    """根据关键词搜索小红书笔记
    
    返回简化后的笔记数据，包含ID、标题、描述、用户信息、互动数据、图片URL列表等。
    如果指定fetch_comments=True，还会包含简化后的评论数据。
    评论数据只包含内容、点赞数和是否有子评论。

    Args:
        keywords: 搜索关键词
        fetch_content: 是否同时获取笔记详细内容，默认为True
        fetch_comments: 是否同时获取笔记评论，默认为False
    """
    try:
        data = await xhs_api.search_notes(keywords, fetch_content=fetch_content, fetch_comments=fetch_comments)
        # logger.info(f'search_notes keywords: {keywords}, response: {data}')
        
        # 直接返回JSON格式的原始数据
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f'search_notes error: {e}')
        error_response = {
            "success": False,
            "error": str(e),
            "data": None,
            "keywords": keywords
        }
        return json.dumps(error_response, ensure_ascii=False, indent=2)


# @mcp.tool()
# async def get_note_content(note_id: str, xsec_token: str) -> str:
#     """获取笔记内容

#     Args:
#         note_id: 笔记ID
#         xsec_token: 用户的xsec_token（可通过home_feed/search_notes获取）
#     """
#     try:
#         data = await xhs_api.get_note_content(note_id, xsec_token)
#         logger.info(f'get_note_content note_id: {note_id}, xsec_token: {xsec_token[:20]}..., response: {data}')
        
#         # 直接返回JSON格式的原始数据
#         return json.dumps(data, ensure_ascii=False, indent=2)
#     except Exception as e:
#         logger.error(f'get_note_content error: {e}')
#         error_response = {
#             "success": False,
#             "error": str(e),
#             "data": None,
#             "note_id": note_id,
#             "xsec_token": xsec_token
#         }
#         return json.dumps(error_response, ensure_ascii=False, indent=2)


# @mcp.tool()
# async def get_note_comments(note_id: str, xsec_token: str) -> str:
#     """获取笔记评论

#     Args:
#         note_id: 笔记ID
#         xsec_token: 用户的xsec_token（可通过home_feed/search_notes获取）
#     """
#     try:
#         data = await xhs_api.get_note_comments(note_id, xsec_token)
#         logger.info(f'get_note_comments note_id: {note_id}, xsec_token: {xsec_token[:20]}..., response: {data}')
        
#         # 直接返回JSON格式的原始数据
#         return json.dumps(data, ensure_ascii=False, indent=2)
#     except Exception as e:
#         logger.error(f'get_note_comments error: {e}')
#         error_response = {
#             "success": False,
#             "error": str(e),
#             "data": None,
#             "note_id": note_id,
#             "xsec_token": xsec_token
#         }
#         return json.dumps(error_response, ensure_ascii=False, indent=2)


# @mcp.tool()
# async def post_comment(comment: str, note_id: str) -> str:
#     """发布评论到指定笔记

#     Args:
#         note_id: 笔记 note_id
#         comment: 要发布的评论内容
#     """
#     try:
#         response = await xhs_api.post_comment(note_id, comment)
#         logger.info(f'post_comment note_id: {note_id}, comment: {comment}, response: {response}')
        
#         # 直接返回JSON格式的原始数据
#         return json.dumps(response, ensure_ascii=False, indent=2)
#     except Exception as e:
#         logger.error(f'post_comment error: {e}')
#         error_response = {
#             "success": False,
#             "error": str(e),
#             "data": None,
#             "note_id": note_id,
#             "comment": comment
#         }
#         return json.dumps(error_response, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    logger.info("mcp run")
    mcp.run(transport=args.type)
