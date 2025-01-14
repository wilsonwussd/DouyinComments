import os
import asyncio
import pandas as pd
from datetime import datetime
from fetch_comments import fetch_all_comments, check_comments_count
from fetch_replies import fetch_replies
from loguru import logger
import random

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
    max_retries = 3
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            cookie = load_cookie()
            
            # 检查评论总数
            try:
                total_comments = await check_comments_count(aweme_id, cookie)
                if total_comments == 0:
                    logger.warning("未检测到评论数量，将使用默认模式")
                else:
                    logger.info(f"检测到总评论数: {total_comments}")
                
                # 根据评论数量选择模式
                use_batch_mode = None  # 让函数自动判断
                if total_comments > 0:
                    use_batch_mode = total_comments > 1000
            except ValueError as e:
                if "Cookie已失效" in str(e) or "视频不存在" in str(e):
                    raise
                logger.warning(f"检查评论数量失败: {str(e)}，将使用默认模式")
                use_batch_mode = None
            
            comments = await fetch_all_comments(aweme_id, cookie, use_batch_mode)
            
            if not comments:
                retry_count += 1
                logger.warning(f"未获取到评论数据，第{retry_count}次重试")
                await asyncio.sleep(2)
                continue
                
            if not isinstance(comments, list):
                logger.error(f"评论数据格式错误: {type(comments)}")
                retry_count += 1
                continue
                
            valid_comments = [c for c in comments if isinstance(c, dict) and "cid" in c and "text" in c]
            if not valid_comments:
                logger.error("没有有效的评论数据")
                retry_count += 1
                continue
                
            logger.info(f"成功获取 {len(valid_comments)} 条有效评论")
            return valid_comments
            
        except ValueError as e:
            error_msg = str(e)
            if any(msg in error_msg for msg in ["Cookie已失效", "视频不存在", "已被删除"]):
                raise  # 这些错误直接抛出，不需要重试
            retry_count += 1
            last_error = error_msg
            logger.warning(f"获取评论出错: {error_msg}，第{retry_count}次重试")
            await asyncio.sleep(2)
        except Exception as e:
            retry_count += 1
            last_error = str(e)
            logger.error(f"获取评论时发生错误: {str(e)}，第{retry_count}次重试")
            await asyncio.sleep(2)
    
    error_msg = f"达到最大重试次数，采集失败。最后一次错误: {last_error}" if last_error else "达到最大重试次数，采集失败"
    raise ValueError(error_msg)  # 改为抛出异常而不是返回None

async def fetch_all_replies_async(comments):
    """异步获取所有回复"""
    try:
        if not comments or not isinstance(comments, list):
            logger.error("评论数据无效")
            return []
            
        cookie = load_cookie()
        all_replies = []
        total_replies = sum(comment.get("reply_comment_total", 0) for comment in comments if isinstance(comment, dict))
        processed_count = 0
        error_count = 0
        max_errors = 3
        
        for comment in comments:
            if not isinstance(comment, dict):
                continue
                
            reply_count = comment.get("reply_comment_total", 0)
            if reply_count > 0:
                try:
                    replies = await fetch_replies(
                        comment.get("aweme_id", ""),
                        comment.get("cid", ""),
                        cookie
                    )
                    
                    if replies and isinstance(replies, list):
                        # 检查重复回复
                        existing_reply_ids = set(reply["cid"] for reply in all_replies if isinstance(reply, dict) and "cid" in reply)
                        unique_replies = [r for r in replies if isinstance(r, dict) and "cid" in r and r["cid"] not in existing_reply_ids]
                        
                        if unique_replies:
                            all_replies.extend(unique_replies)
                            processed_count += 1
                            logger.info(f"已处理 {processed_count}/{total_replies} 个评论的回复")
                            error_count = 0  # 重置错误计数
                        else:
                            logger.warning(f"评论 {comment.get('cid', '')} 未获取到有效回复")
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"获取评论 {comment.get('cid', '')} 的回复时出错: {str(e)}")
                    if error_count >= max_errors:
                        logger.error("连续错误次数过多，跳过剩余回复获取")
                        break
                    continue
                
                # 添加随机延时
                await asyncio.sleep(random.uniform(1, 2))
        
        return all_replies
    except Exception as e:
        logger.error(f"获取回复时发生错误: {str(e)}")
        raise

def process_comments(comments):
    """处理评论数据"""
    if not comments or not isinstance(comments, list):
        logger.warning("没有有效的评论数据可以处理")
        return pd.DataFrame()
        
    data = []
    error_count = 0
    
    for comment in comments:
        try:
            # 添加更多错误检查
            if not isinstance(comment, dict):
                error_count += 1
                continue
                
            user = comment.get("user", {})
            if not isinstance(user, dict):
                error_count += 1
                continue
                
            create_time = comment.get("create_time", 0)
            if not isinstance(create_time, (int, float)):
                create_time = 0
            
            cid = comment.get("cid", "")
            if not cid:
                error_count += 1
                continue
                
            data.append({
                "评论ID": cid,
                "评论内容": comment.get("text", ""),
                "点赞数": int(comment.get("digg_count", 0)),
                "评论时间": datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S"),
                "用户昵称": user.get("nickname", "未知"),
                "用户抖音号": user.get("unique_id", "未设置"),
                "ip归属": comment.get("ip_label", "未知"),
                "回复总数": int(comment.get("reply_comment_total", 0))
            })
        except Exception as e:
            error_count += 1
            logger.error(f"处理评论数据时出错: {str(e)}, 评论数据: {comment}")
            continue
            
    if error_count > 0:
        logger.warning(f"处理评论数据时有 {error_count} 条记录出错")
        
    if not data:
        logger.warning("没有有效的评论数据可以处理")
        return pd.DataFrame()
        
    return pd.DataFrame(data)

def process_replies(replies, comments_df):
    """处理回复数据"""
    if not replies or not isinstance(replies, list):
        return pd.DataFrame()
        
    data = []
    error_count = 0
    
    for reply in replies:
        try:
            if not isinstance(reply, dict):
                error_count += 1
                continue
                
            user = reply.get("user", {})
            if not isinstance(user, dict):
                error_count += 1
                continue
                
            create_time = reply.get("create_time", 0)
            if not isinstance(create_time, (int, float)):
                create_time = 0
                
            cid = reply.get("cid", "")
            if not cid:
                error_count += 1
                continue
                
            data.append({
                "评论ID": cid,
                "评论内容": reply.get("text", ""),
                "点赞数": int(reply.get("digg_count", 0)),
                "评论时间": datetime.fromtimestamp(create_time).strftime("%Y-%m-%d %H:%M:%S"),
                "用户昵称": user.get("nickname", "未知"),
                "用户抖音号": user.get("unique_id", "未设置"),
                "ip归属": reply.get("ip_label", "未知"),
                "回复总数": 0  # 二级评论没有回复
            })
        except Exception as e:
            error_count += 1
            logger.error(f"处理回复数据时出错: {str(e)}, 回复数据: {reply}")
            continue
            
    if error_count > 0:
        logger.warning(f"处理回复数据时有 {error_count} 条记录出错")
        
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
