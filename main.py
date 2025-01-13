import os
import asyncio
import pandas as pd
from datetime import datetime
from fetch_comments import fetch_all_comments
from fetch_replies import fetch_replies
from loguru import logger

def load_cookie():
    """从环境变量或文件加载cookie"""
    cookie = os.getenv("DOUYIN_COOKIE")
    if cookie:
        logger.info("从环境变量加载cookie成功")
        return cookie
        
    cookie_file = "cookie.txt"
    if not os.path.exists(cookie_file):
        raise Exception("Cookie未加载，请先设置DOUYIN_COOKIE环境变量或创建cookie.txt文件")
        
    with open(cookie_file, "r", encoding="utf-8") as f:
        cookie = f.read().strip()
        if not cookie:
            raise Exception("Cookie文件为空")
    
    logger.info("从文件加载cookie成功")
    return cookie

async def fetch_all_comments_async(aweme_id):
    """异步获取所有评论"""
    try:
        cookie = load_cookie()
        return await fetch_all_comments(aweme_id, cookie)
    except Exception as e:
        logger.error(f"获取评论时发生错误: {str(e)}")
        return None

async def fetch_all_replies_async(comments):
    """异步获取所有回复"""
    try:
        cookie = load_cookie()
        all_replies = []
        for comment in comments:
            if comment.get("reply_comment_total", 0) > 0:
                replies = await fetch_replies(
                    comment["aweme_id"],
                    comment["cid"],
                    cookie
                )
                if replies:
                    all_replies.extend(replies)
        return all_replies
    except Exception as e:
        logger.error(f"获取回复时发生错误: {str(e)}")
        return []

def process_comments(comments):
    """处理评论数据"""
    if not comments:
        return pd.DataFrame()
        
    data = []
    for comment in comments:
        try:
            data.append({
                "评论ID": comment.get("cid", ""),
                "评论内容": comment.get("text", ""),
                "点赞数": comment.get("digg_count", 0),
                "评论时间": datetime.fromtimestamp(comment.get("create_time", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                "用户昵称": comment.get("user", {}).get("nickname", "未知"),
                "用户抖音号": comment.get("user", {}).get("unique_id", "未设置"),
                "ip归属": comment.get("ip_label", "未知"),
                "回复总数": comment.get("reply_comment_total", 0)
            })
        except Exception as e:
            logger.error(f"处理评论数据时出错: {str(e)}, 评论数据: {comment}")
            continue
    return pd.DataFrame(data)

def process_replies(replies, comments_df):
    """处理回复数据"""
    if not replies:
        return pd.DataFrame()
        
    data = []
    for reply in replies:
        try:
            data.append({
                "评论ID": reply.get("cid", ""),
                "评论内容": reply.get("text", ""),
                "点赞数": reply.get("digg_count", 0),
                "评论时间": datetime.fromtimestamp(reply.get("create_time", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                "用户昵称": reply.get("user", {}).get("nickname", "未知"),
                "用户抖音号": reply.get("user", {}).get("unique_id", "未设置"),
                "ip归属": reply.get("ip_label", "未知"),
                "回复总数": 0  # 二级评论没有回复
            })
        except Exception as e:
            logger.error(f"处理回复数据时出错: {str(e)}, 回复数据: {reply}")
            continue
    return pd.DataFrame(data)

async def main_async():
    """异步主函数"""
    # 获取视频ID
    aweme_id = input("请输入视频ID: ").strip()
    if not aweme_id:
        logger.error("视频ID不能为空")
        return
        
    # 获取评论
    comments = await fetch_all_comments_async(aweme_id)
    if not comments:
        logger.error("未获取到评论数据")
        return
        
    comments_df = process_comments(comments)
    logger.info(f"成功获取 {len(comments)} 条评论")
    
    # 询问是否获取回复
    get_replies = input("是否获取评论的回复？(y/n): ").strip().lower() == 'y'
    if get_replies:
        replies = await fetch_all_replies_async(comments)
        logger.info(f"成功获取 {len(replies)} 条回复")
        replies_df = process_replies(replies, comments_df)
        result = pd.concat([comments_df, replies_df], ignore_index=True)
    else:
        result = comments_df
    
    # 保存数据
    save_dir = f"data/v1/{aweme_id}"
    os.makedirs(save_dir, exist_ok=True)
    result.to_csv(f"{save_dir}/comments.csv", index=False, encoding="utf-8-sig")
    logger.info(f"数据已保存到 {save_dir}/comments.csv")

if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
