import asyncio
import httpx
from loguru import logger
from common import common

# 配置常量
url = "https://www.douyin.com/aweme/v1/web/comment/list/"

async def fetch_comments(aweme_id: str, cookie: str, cursor: str = "0", count: str = "100"):
    """获取评论数据"""
    try:
        if not cookie:
            raise ValueError("Cookie不能为空")
            
        params = {
            "aweme_id": aweme_id,
            "cursor": cursor,
            "count": count,
            "item_type": 0
        }
        headers = {"cookie": cookie}
        
        # 使用common模块处理参数
        params, headers = common(url, params, headers)
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status_code") != 0:
                raise ValueError(f"请求失败: {data.get('status_msg', '未知错误')}")
                
            return data.get("comments", []), data.get("has_more", 0), data.get("cursor", cursor)
            
    except httpx.HTTPError as e:
        logger.error(f"获取评论时发生网络错误: {str(e)}")
        return [], 0, cursor
    except Exception as e:
        logger.error(f"获取评论时发生错误: {str(e)}")
        return [], 0, cursor

async def fetch_all_comments(aweme_id: str, cookie: str):
    """获取所有评论"""
    try:
        cursor = "0"
        all_comments = []
        has_more = 1
        
        while has_more:
            comments, has_more, next_cursor = await fetch_comments(aweme_id, cookie, cursor)
            if not comments:
                break
                
            all_comments.extend(comments)
            logger.info(f"已获取 {len(all_comments)} 条评论")
            
            # 更新cursor
            cursor = next_cursor
            
            # 添加延时避免请求过快
            await asyncio.sleep(1)
            
        return all_comments
        
    except Exception as e:
        logger.error(f"获取所有评论时发生错误: {str(e)}")
        return []
