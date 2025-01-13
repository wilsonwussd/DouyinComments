import asyncio
import httpx
from loguru import logger
from common import common

# 配置常量
url = "https://www.douyin.com/aweme/v1/web/comment/list/reply/"

async def fetch_replies(aweme_id: str, comment_id: str, cookie: str, cursor: str = "0", count: str = "50"):
    """获取评论回复数据"""
    try:
        if not cookie:
            raise ValueError("Cookie不能为空")
            
        params = {
            "item_id": aweme_id,
            "comment_id": comment_id,
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
                
            return data.get("comments", [])
            
    except httpx.HTTPError as e:
        logger.error(f"获取回复时发生网络错误: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"获取回复时发生错误: {str(e)}")
        return []

async def fetch_all_replies(aweme_id: str, comment_id: str, cookie: str):
    """获取评论的所有回复"""
    try:
        cursor = "0"
        all_replies = []
        has_more = True
        
        while has_more:
            replies = await fetch_replies(aweme_id, comment_id, cookie, cursor)
            if not replies:
                break
                
            all_replies.extend(replies)
            logger.info(f"已获取评论 {comment_id} 的 {len(all_replies)} 条回复")
            
            # 检查是否还有更多回复
            has_more = len(replies) == 50  # 如果返回的回复数量等于请求的数量，说明可能还有更多
            cursor = str(len(all_replies))  # 更新cursor
            
            # 添加延时避免请求过快
            await asyncio.sleep(1)
            
        return all_replies
        
    except Exception as e:
        logger.error(f"获取所有回复时发生错误: {str(e)}")
        return []
