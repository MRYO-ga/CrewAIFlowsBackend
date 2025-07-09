import asyncio
import json
import time
import logging
from collections.abc import Mapping
from urllib.parse import urlencode
import requests
from curl_cffi.requests import AsyncSession, Response
from datetime import datetime
from typing import Dict, List, Any
import os
import execjs
from numbers import Integral
from typing import Iterable, List, Optional, Tuple
import random
import base64

# 设置日志记录器
logger = logging.getLogger(__name__)

class XhsApi:
    def __init__(self,cookie):
        self._cookie=cookie
        self._base_url="https://edith.xiaohongshu.com"
        self._headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
    def init_session(self):
        return AsyncSession(
            verify=True,
            impersonate="chrome123"
        )

    def _parse_cookie(self, cookie: str) -> Dict:

        cookie_dict = {}
        if cookie:
            pairs = cookie.split(';')
            for pair in pairs:
                key, value = pair.strip().split('=', 1)
                cookie_dict[key] = value
        return cookie_dict
        
    async def _process_note_data(self, item: Dict, fetch_comments: bool = False) -> Dict:
        """处理笔记数据，提取所需字段并生成笔记URL
        
        Args:
            item: 原始笔记数据
            fetch_comments: 是否获取评论数据
            
        Returns:
            Dict: 处理后的笔记数据
        """
        try:
            result = {
                "id": item.get("id", ""),
                "model_type": item.get("model_type", ""),
                "xsec_token": item.get("xsec_token", ""),
            }
            
            # 生成笔记URL
            result["note_url"] = f'https://www.xiaohongshu.com/explore/{result["id"]}?xsec_token={result["xsec_token"]}'
            
            # 处理note_card数据
            if "note_card" in item:
                note_card = item["note_card"]
                
                # 基本信息
                result["type"] = note_card.get("type", "")
                result["display_title"] = note_card.get("display_title", note_card.get("title", ""))
                result["desc"] = note_card.get("desc", "")
                result["ip_location"] = note_card.get("ip_location", "")
                
                # 时间处理（转换为可读格式）
                if "time" in note_card:
                    timestamp_ms = note_card["time"]
                    try:
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        result["time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        result["timestamp"] = timestamp_ms
                    except Exception as e:
                        logger.error(f"时间转换失败: {e}")
                        result["time"] = ""
                        result["timestamp"] = 0
                
                if "last_update_time" in note_card:
                    timestamp_ms = note_card["last_update_time"]
                    try:
                        dt = datetime.fromtimestamp(timestamp_ms / 1000)
                        result["last_update_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        logger.error(f"更新时间转换失败: {e}")
                        result["last_update_time"] = ""
                
                # 用户信息
                if "user" in note_card:
                    user = note_card["user"]
                    result["user"] = {
                        "user_id": user.get("user_id", ""),
                        "nickname": user.get("nickname", ""),
                        "avatar": user.get("avatar", ""),
                        "xsec_token": user.get("xsec_token", "")
                    }
                
                # 互动信息
                if "interact_info" in note_card:
                    interact = note_card["interact_info"]
                    result["interact_info"] = {
                        "liked_count": interact.get("liked_count", "0"),
                        "collected_count": interact.get("collected_count", "0"),
                        "comment_count": interact.get("comment_count", "0"),
                        "share_count": interact.get("share_count", "0"),
                    }
                
                # 封面图片
                if "cover" in note_card and "url_default" in note_card["cover"]:
                    result["cover_image"] = note_card["cover"]["url_default"]
                
                # 图片列表 - 只保存URL列表
                result["images"] = []
                if "image_list" in note_card:
                    for img in note_card["image_list"]:
                        if "url_default" in img:
                            result["images"].append(img["url_default"])
            
            # 处理详情数据
            if "note_detail" in item and item["note_detail"].get("success", False):
                detail_data = item["note_detail"]["data"]
                if "items" in detail_data and len(detail_data["items"]) > 0:
                    detail_item = detail_data["items"][0]
                    if "note_card" in detail_item:
                        detail_card = detail_item["note_card"]
                        
                        # 如果没有描述，从详情中获取
                        if not result.get("desc") and "desc" in detail_card:
                            result["desc"] = detail_card.get("desc", "")
                        
                        # 如果没有位置信息，从详情中获取
                        if not result.get("ip_location") and "ip_location" in detail_card:
                            result["ip_location"] = detail_card.get("ip_location", "")
                        
                        # 如果没有图片，从详情中获取
                        if not result.get("images") and "image_list" in detail_card:
                            result["images"] = []
                            for img in detail_card["image_list"]:
                                if "url_default" in img:
                                    result["images"].append(img["url_default"])
            
            # 获取评论数据
            if fetch_comments and result["id"] and result["xsec_token"]:
                try:
                    # 添加延时避免请求过于频繁
                    await asyncio.sleep(1)
                    comments_data = await self.get_note_comments(result["id"], result["xsec_token"])
                    
                    # 简化评论数据
                    simplified_comments = []
                    if comments_data.get("success", False) and "data" in comments_data and "comments" in comments_data["data"]:
                        for comment in comments_data["data"]["comments"]:
                            simplified_comment = {
                                "content": comment.get("content", ""),
                                "like_count": comment.get("like_count", 0),
                                "sub_comment_has_more": comment.get("sub_comment_has_more", False)
                            }
                            simplified_comments.append(simplified_comment)
                    
                    result["comments"] = simplified_comments
                except Exception as e:
                    logger.error(f"获取评论失败: {result['id']}, 错误: {e}")
                    result["comments"] = []
            
            return result
        except Exception as e:
            logger.error(f"处理笔记数据失败: {e}")
            return {
                "id": item.get("id", ""),
                "error": f"处理数据失败: {e}",
                "raw_data": item
            }
            
    async def _process_response_data(self, data: Dict, fetch_comments: bool = False) -> Dict:
        """处理API响应数据，简化笔记内容
        
        Args:
            data: 原始API响应数据
            fetch_comments: 是否获取评论数据
            
        Returns:
            Dict: 处理后的响应数据
        """
        try:
            result = {
                "success": data.get("success", False),
                "msg": data.get("msg", ""),
                "code": data.get("code", -1),
            }
            
            if "data" in data:
                result_data = {}
                
                # 添加分页信息 - 移除cursor_score
                if "has_more" in data["data"]:
                    result_data["has_more"] = data["data"]["has_more"]
                if "current_time" in data["data"]:
                    result_data["current_time"] = data["data"]["current_time"]
                
                # 处理笔记列表
                result_data["items"] = []
                if "items" in data["data"]:
                    for item in data["data"]["items"]:
                        processed_item = await self._process_note_data(item, fetch_comments)
                        result_data["items"].append(processed_item)
                
                result["data"] = result_data
            
            return result
        except Exception as e:
            logger.error(f"处理响应数据失败: {e}")
            return {
                "success": False,
                "msg": f"处理响应数据失败: {e}",
                "raw_data": data
            }

    async def request(self,uri: str,session=None, method="GET",headers=None,params=None,data=None) -> Dict:
        if session is None:
            session=self.init_session()
        if headers is None:
            headers = {}
        response: Response = await session.request(
            method=method,
            url=f"{self._base_url}{uri}",
            params=params,
            json=data,
            cookies=self._parse_cookie(self._cookie),
            stream=True,
            headers=headers
        )


        content = await response.acontent()
        
        # 添加调试信息
        # logger.info(f"API 响应状态码: {response.status_code}")
        # logger.info(f"API 响应内容长度: {len(content)}")
        # logger.info(f"API 响应内容前200字符: {repr(content[:500])}")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"完整响应内容: {repr(content)}")
            # 返回错误信息而不是抛出异常
            return {
                "success": False,
                "error": f"JSON 解析失败: {e}",
                "data": None,
                "raw_content": content.decode('utf-8', errors='ignore') if isinstance(content, bytes) else str(content)
            }
    def base36encode(self,number: Integral, alphabet: Iterable[str] = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') -> str:

        base36 = ''
        alphabet = ''.join(alphabet)
        sign = '-' if number < 0 else ''
        number = abs(number)

        while number:
            number, i = divmod(number, len(alphabet))
            base36 = alphabet[i] + base36

        return sign + (base36 or alphabet[0])

    def search_id(self):
        e = int(time.time() * 1000) << 64
        t = int(random.uniform(0, 2147483646))
        return self.base36encode((e + t))

    def get_xs_xt(self,uri, data, cookie):
        current_directory = os.path.dirname(__file__)
        file_path = os.path.join(current_directory, "xhsvm.js")
        return execjs.compile(open(file_path, 'r', encoding='utf-8').read()).call('GetXsXt', uri, data, cookie)

    async def get_me(self) -> Dict:
        uri = '/api/sns/web/v2/user/me'
        return await self.request(uri,method="GET")

    async def search_notes(self, keywords: str, limit: int = 20, fetch_content: bool = True, fetch_comments: bool = False) -> Dict:
        data={
            "keyword":keywords,
            "page":1,
            "page_size":limit,
            "search_id":self.search_id(),
            "sort":"general",
            "note_type":0,
            "ext_flags":[],
            "geo":"",
            "image_formats":json.dumps(["jpg","webp","avif"], separators=(",", ":"))
        }
        result = await self.request("/api/sns/web/v1/search/notes",method="POST",data=data)
        
        # 如果需要获取笔记内容并且请求成功
        if fetch_content and 'success' in result and result['success'] and 'data' in result and 'items' in result['data']:
            for item in result['data']['items']:
                if 'id' in item and 'xsec_token' in item:
                    note_id = item['id']
                    xsec_token = item['xsec_token']
                    try:
                        # 添加延时，避免请求过于频繁
                        await asyncio.sleep(1)
                        
                        # 获取笔记详细内容
                        note_content = await self.get_note_content(note_id, xsec_token)
                        # 将笔记内容添加到结果中
                        item['note_detail'] = note_content
                    except Exception as e:
                        logger.error(f"获取笔记内容失败: {note_id}, 错误: {e}")
                        item['note_detail'] = {"success": False, "error": str(e)}
        
        # 简化数据
        return await self._process_response_data(result, fetch_comments)

    async def home_feed(self, fetch_content: bool = True, fetch_comments: bool = False) -> Dict:

        data={
            "category":"homefeed_recommend",
            "cursor_score":"",
            "image_formats":json.dumps(["jpg","webp","avif"], separators=(",", ":")),
            "need_filter_image":False,
            "need_num":8,
            "num":18,
            "note_index":33,
            "refresh_type":1,
            "search_key":"",
            "unread_begin_note_id":"",
            "unread_end_note_id":"",
            "unread_note_count":0
        }
        uri="/api/sns/web/v1/homefeed"
        p={"uri":uri,"method":"POST","data":data}
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        xsxt=json.loads(self.get_xs_xt(uri,data,self._cookie))
        headers['x-s']=xsxt['X-s']
        headers['x-t']=str(xsxt['X-t'])
        result = await self.request(**p,headers=headers)
        
        # 如果需要获取笔记内容并且请求成功
        if fetch_content and 'success' in result and result['success'] and 'data' in result and 'items' in result['data']:
            # 只获取前3条笔记的详细内容，避免请求过多被限制
            max_fetch_count = len(result['data']['items'])
            
            for i, item in enumerate(result['data']['items']):
                if i >= max_fetch_count:
                    item['note_detail'] = {"success": False, "error": "跳过获取详情以避免请求过多"}
                    continue
                    
                if 'id' in item and 'xsec_token' in item:
                    note_id = item['id']
                    xsec_token = item['xsec_token']
                    try:
                        # 添加延时，避免请求过于频繁
                        await asyncio.sleep(1)
                        
                        # 获取笔记详细内容（最多尝试2次）
                        retries = 1
                        for attempt in range(retries):
                            try:
                                note_content = await self.get_note_content(note_id, xsec_token)
                                # 将笔记内容添加到结果中
                                item['note_detail'] = note_content
                                break
                            except Exception as e:
                                logger.error(f"获取笔记内容失败(尝试 {attempt+1}/{retries}): {note_id}, 错误: {e}")
                                if attempt == retries - 1:  # 最后一次尝试失败
                                    item['note_detail'] = {"success": False, "error": str(e)}
                                else:
                                    # 重试前等待更长时间
                                    await asyncio.sleep(3)
                    except Exception as e:
                        logger.error(f"获取笔记内容失败: {note_id}, 错误: {e}")
                        item['note_detail'] = {"success": False, "error": str(e)}
        
        # 简化数据
        return await self._process_response_data(result, fetch_comments)

    async def get_note_content(self, note_id: str, xsec_token: str) -> Dict:
        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg","webp","avif"],
            "extra": {"need_body_topic":"1"},
            "xsec_source": "pc_feed",
            "xsec_token": xsec_token
        }
        uri="/api/sns/web/v1/feed"
        p={"uri":uri,"method":"POST","data":data}
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        xsxt=json.loads(self.get_xs_xt(uri,data,self._cookie))
        headers['x-s']=xsxt['X-s']
        headers['x-t']=str(xsxt['X-t'])
        headers['x-s-common']='2UQAPsHCPUIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PahIHjIj2eHjwjQ+GnPW/MPjNsQhPUHCHdYiqUMIGUM78nHjNsQh+sHCH0c1+0H1PUHVHdWMH0ijP/DAP9L9P/DhPerUJoL72nIM+9Qf8fpC2fHA8n4Fy0m1Gnpd4n+I+BHAPeZIPerMw/GhPjHVHdW9H0il+Ac7weZ7PAWU+/LUNsQh+UHCHSY8pMRS2LkCGp4D4pLAndpQyfRk/Sz8yLleadkYp9zMpDYV4Mk/a/8QJf4EanS7ypSGcd4/pMbk/9St+BbH/gz0zFMF8eQnyLSk49S0Pfl1GflyJB+1/dmjP0zk/9SQ2rSk49S0zFGMGDqEybkea/8QJLkx/fkb+pkgpfYwpFSE/p4Q4MkLp/+ypMph/dkDJpkTp/p+pB4C/F4ayDETn/Qw2fPI/Szz4MSgngkwPSk3nSzwyDRrp/myySLF/dkp2rMra/QypMDlnnM8PrEL/fMypMLA/L4aybkLz/p+pMQT/LzQ+LRLc/+8yfzVnD4+2bkLzflwzbQx/nktJLELngY+yfVMngktJrEr/gY+ySrF/nkm2DFUnfkwJL83nD4zPFMgz/+Ozrk3/Lz8+pkrafkyprbE/M4p+pkrngYypbphnnM+PMkxcg482fYxnD4p+rExyBMyzFFl/dk0PFMCp/pOzrFM/Dz04FECcg4yzBzingkz+LMCafS+pMQi/fM8PDEx/gYyzFEinfM8PLETpg4wprDM/0QwJbSgzg4OpBTCnDz+4MSxy74wySQx/L4tJpkLngSwzB4hn/QbPrErL/zwJLMh/gkp2SSLa/bwzFEknpzz2LMx/gSwpMDA//Qz4Mkr/fMwzrLA/nMzPSkTnfk+2fVM/pzpPMkrzfY8pFDInS4ayLELafSOzbb7npzDJpkLy7kwzBl3/gkDyDRL87Y+yDMC/DzaJpkrLg4+PSkknDzQ4FEoL/zwpBVUngkVyLMoL/m8JLp7/nMyJLMC8BTwpbphnDziyLExzgY+yDEinpzz2pkTpgk8yDbC/0QByFMTn/zOzbDl/LziJpSLcgYypFDlnnMQPFMC8A+ypBVl/gk32pkLL/++zFk3anhIOaHVHdWhH0ija/PhqDYD87+xJ7mdag8Sq9zn494QcUT6aLpPJLQy+nLApd4G/B4BprShLA+jqg4bqD8S8gYDPBp3Jf+m2DMBnnEl4BYQyrkSL9zL2obl49zQ4DbApFQ0yo4c4ozdJ/c9aMpC2rSiPoPI/rTAydb7JdD7zbkQ4fRA2BQcydSy4LbQyrTSzBr7q98ppbztqgzat7b7cgmDqrEQc9YT/Sqha7kn4M+Qc94Sy7pFao4l4FzQzL8laLL6qMzQnfSQ2oQ+ag8d8nzl4MH3+7mc2Skwq9z8P9pfqgzmanTw8/+n494lqgzIqopF2rTC87Plp7mSaL+npFSiL/Z6LozzaM87cLDAn0Q6JnzSygb78DSecnpLpdzUaLL3tFSbJnE08fzSyf4CngQ6J7+fqg4OnS468nzPzrzsJ94AySkIcDSha7+DpdzYanT98n8l4MQj/LlQz9GFcDDA+7+hqgzbNM4O8gWIJezQybbAaLLhtFYd/B8Q2rpAwrMVJLS3G98jLo4/aL+lpAYdad+8nLRAyMm7LDDAa9pfcDbS8eZFtFSbPo+hGfMr4bm7yDS3a9LA878ApfF6qAbc4rEINFRSydp7pDS9zn4Ccg8SL7p74Dlsad+/4gq3a/PhJDDAwepT4g4oJpm7afRmy/zNpFESzBqM8/8l49+QyBpAzeq98/bCL0SQzLEA8DMSqA8xG9lQyFESPMmFprSkG0mELozIaSm78rSh8npkpdzBaLLIqMzM4M+QysRAzopFL74M47+6pdzGag8HpLDAagrFGgmaLLzdqA+l4r+Q2BM+anTtqFzl4obPzsTYJAZIq9cIaB8QygQsz7pFJ7QM49lQ4DESpSmFnaTBa9pkGFEAyLSC8LSi87P9JA8ApopFqURn47bQPFbSPob7yrS389L9q7pPaL+D8pSA4fpfLoz+a/P7qM8M47pOcLclanS84FSh8BL92DkA2bSdqFzyP9prpd4YanW3pFSezfV6Lo41a/+rpDSkafpnagk+2/498n8n4AQQyMZ6JSm7anMU8nLIaLbA8dpF8Lll4rRQy9D9aLpz+bmn4oSOqg4Ca/P6q9kQ+npkLo4lqgbFJDSi+ezA4gc9a/+ynSkSzFkQynzAzeqAq9k68Bp34gqhaopFtFSknSbQP9zA+dpFpDSkJ9p8zrpfag8aJ9RgL9+Qzp+SaL+m8/bl4Mq6pdc3/S8FJrShLr+QzLbAnnLI8/+l4A+IGdQeag8c8AYl4sTOLoz+anTUarS3JpSQPMQPagGI8nzj+g+/L7i94M8FnDDAap4Y4g4YGdp7pFSiPBp3+7QGanSccLldPBprLozk8gpFJnRCLB+7+9+3anTzyomM47pQyFRAPnF3GFS3LfRFpd4FagY/pfMl4sTHpdzNaL+/aLDAy9VjNsQhwaHCP/HlweGM+/Z9PjIj2erIH0iU+emR'
        
        try:
            return await self.request(**p,headers=headers)
        except Exception as e:
            # 捕获请求异常，记录日志
            logger.error(f"get_note_content请求失败: {note_id}, 错误: {e}")
            # 向上层传递异常，让调用者处理
            raise

    async def get_note_comments(self,note_id:str,xsec_token:str) -> Dict:
        uri = '/api/sns/web/v2/comment/page'
        # 680a25a4000000001c02d251
        # ABzm9YfVyNA1hsY-KwU7ybKNWlkpb8__t-jF9FwGKzZz0=
        params = {
            'note_id': note_id,
            'cursor': '',
            'top_comment_id': '',
            'image_formats': 'jpg,webp,avif',
            'xsec_token': xsec_token
        }


        return await self.request(uri,method="GET",params=params)

    async def post_comment(self,note_id:str, comment: str) -> Dict:
        uri='/api/sns/web/v1/comment/post'
        # 680ce9d1000000001c02cb9f
        data={
            "note_id":note_id,
            "content":comment,
            "at_users":[]
        }
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        xsxt = json.loads(self.get_xs_xt(uri, data, self._cookie))
        headers['x-s'] = xsxt['X-s']
        headers['x-t'] = str(xsxt['X-t'])
        return await self.request(uri, method="POST",headers=headers, data=data)

