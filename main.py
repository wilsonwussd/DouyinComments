import asyncio
from datetime import datetime
from typing import Any
import os
import httpx
import pandas as pd
from tqdm import tqdm
from common import common
from loguru import logger
import sys
from retry import retry

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add("error.log", rotation="500 MB", level="ERROR", encoding="utf-8")

# 配置常量
url = "https://www.douyin.com/aweme/v1/web/comment/list/"
reply_url = url + "reply/"
cookie = None  # 全局cookie变量

def load_cookie():
    """加载cookie文件"""
    global cookie
    try:
        with open('cookie.txt', 'r') as f:
            cookie = f.readline().strip()
            return cookie
    except FileNotFoundError:
        logger.error("cookie.txt 文件不存在！请先创建该文件并填入cookie。")
        raise
    except Exception as e:
        logger.error(f"读取cookie时发生错误: {str(e)}")
        raise

@retry(tries=3, delay=2)
async def get_comments_async(client: httpx.AsyncClient, aweme_id: str, cursor: str = "0", count: str = "50") -> dict[str, Any]:
    """获取评论数据，支持自动重试"""
    try:
        if cookie is None:
            raise ValueError("Cookie未加载，请先调用load_cookie()")
            
        params = {"aweme_id": aweme_id, "cursor": cursor, "count": count, "item_type": 0}
        headers = {"cookie": cookie}
        params, headers = common(url, params, headers)
        response = await client.get(url, params=params, headers=headers)
        await asyncio.sleep(0.8)
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"获取评论时发生网络错误: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"解析评论数据时发生错误: {str(e)}")
        return {}



async def fetch_all_comments_async(aweme_id: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=600) as client:
        cursor = 0
        all_comments = []
        has_more = 1
        with tqdm(desc="Fetching comments", unit="comment") as pbar:
            while has_more:
                response = await get_comments_async(client, aweme_id, cursor=str(cursor))
                comments = response.get("comments", [])
                if isinstance(comments, list):
                    all_comments.extend(comments)
                    pbar.update(len(comments))
                has_more = response.get("has_more", 0)
                if has_more:
                    cursor = response.get("cursor", 0)
                await asyncio.sleep(1)
        return all_comments


async def get_replies_async(client: httpx.AsyncClient, semaphore, comment_id: str, cursor: str = "0",
                            count: str = "50") -> dict:
    if cookie is None:
        raise ValueError("Cookie未加载，请先调用load_cookie()")
        
    params = {"cursor": cursor, "count": count, "item_type": 0, "item_id": comment_id, "comment_id": comment_id}
    headers = {"cookie": cookie}
    params, headers = common(reply_url, params, headers)
    async with semaphore:
        response = await client.get(reply_url, params=params, headers=headers)
        await asyncio.sleep(0.3)
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"解析回复数据时发生错误: {str(e)}")
            return {}


async def fetch_replies_for_comment(client: httpx.AsyncClient, semaphore, comment: dict, pbar: tqdm) -> list:
    comment_id = comment["cid"]
    has_more = 1
    cursor = 0
    all_replies = []
    while has_more and comment["reply_comment_total"] > 0:
        response = await get_replies_async(client, semaphore, comment_id, cursor=str(cursor))
        replies = response.get("comments", [])
        if isinstance(replies, list):
            all_replies.extend(replies)
        has_more = response.get("has_more", 0)
        if has_more:
            cursor = response.get("cursor", 0)
        await asyncio.sleep(0.5)
    pbar.update(1)
    return all_replies


async def fetch_all_replies_async(comments: list) -> list:
    all_replies = []
    async with httpx.AsyncClient(timeout=600) as client:
        semaphore = asyncio.Semaphore(10)  # 在这里创建信号量
        with tqdm(total=len(comments), desc="Fetching replies", unit="comment") as pbar:
            tasks = [fetch_replies_for_comment(client, semaphore, comment, pbar) for comment in comments]
            results = await asyncio.gather(*tasks)
            for result in results:
                all_replies.extend(result)
    return all_replies


def process_comments(comments: list[dict[str, Any]]) -> pd.DataFrame:
    data = [{
        "评论ID": c['cid'],
        "评论内容": c['text'],
        "评论图片": c['image_list'][0]['origin_url']['url_list'] if c['image_list'] else None,
        "点赞数": c['digg_count'],
        "评论时间": datetime.fromtimestamp(c['create_time']).strftime('%Y-%m-%d %H:%M:%S'),
        "用户昵称": c['user']['nickname'],
        "用户主页链接": f"https://www.douyin.com/user/{c['user']['sec_uid']}",
        "用户抖音号": c['user'].get('unique_id', '未知'),
        "用户签名": c['user'].get('signature', '未知'),
        "回复总数": c['reply_comment_total'],
        "ip归属":c['ip_label']
    } for c in comments]
    return pd.DataFrame(data)


def process_replies(replies: list[dict[str, Any]], comments: pd.DataFrame) -> pd.DataFrame:
    data = [
        {
            "评论ID": c["cid"],
            "评论内容": c["text"],
            "评论图片": c['image_list'][0]['origin_url']['url_list'] if c['image_list'] else None,
            "点赞数": c["digg_count"],
            "评论时间": datetime.fromtimestamp(c["create_time"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "用户昵称": c["user"]["nickname"],
            "用户主页链接": f"https://www.douyin.com/user/{c['user']['sec_uid']}",
            "用户抖音号": c['user'].get('unique_id', '未知'),
            "用户签名": c['user'].get('signature', '未知'),
            "回复的评论": c["reply_id"],
            "具体的回复对象": c["reply_to_reply_id"]
            if c["reply_to_reply_id"] != "0"
            else c["reply_id"],
            "回复给谁": comments.loc[comments['评论ID'] == c["reply_id"], '用户昵称'].values[0]
            if c["reply_to_reply_id"] == "0"
            else c["reply_to_username"],
            "ip归属":c.get('ip_label','未知')
        }
        for c in replies
    ]
    return pd.DataFrame(data)


def save(data: pd.DataFrame, filename: str):
    data.to_csv(filename, index=False)





async def main():
    try:
        logger.info("开始运行抖音评论采集工具...")
        
        # 获取视频ID
        aweme_id = input("请输入抖音视频ID (在视频链接中找到): ").strip()
        if not aweme_id:
            logger.error("视频ID不能为空！")
            return
            
        # 评论部分
        logger.info("开始获取评论数据...")
        all_comments = await fetch_all_comments_async(aweme_id)
        logger.success(f"成功获取 {len(all_comments)} 条评论！")
        
        all_comments_ = process_comments(all_comments)
        base_dir = f"data/v1/{aweme_id}"
        os.makedirs(base_dir, exist_ok=True)
        comments_file = os.path.join(base_dir, "comments.csv")
        save(all_comments_, comments_file)
        logger.success(f"评论数据已保存到: {comments_file}")

        # 询问是否获取回复
        get_replies = input("是否获取评论的回复？(y/n): ").strip().lower()
        if get_replies == 'y':
            logger.info("开始获取回复数据...")
            all_replies = await fetch_all_replies_async(all_comments)
            logger.success(f"成功获取 {len(all_replies)} 条回复！")
            logger.info(f"总计获取 {len(all_replies) + len(all_comments)} 条数据")
            
            all_replies = process_replies(all_replies, all_comments_)
            replies_file = os.path.join(base_dir, "replies.csv")
            save(all_replies, replies_file)
            logger.success(f"回复数据已保存到: {replies_file}")
        
        logger.success("数据采集完成！")
        
    except KeyboardInterrupt:
        logger.warning("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        logger.exception(e)
    finally:
        logger.info("程序结束运行")


# 运行 main 函数
if __name__ == "__main__":
    cookie = load_cookie()
    asyncio.run(main())
    print('done!')
