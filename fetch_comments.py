import asyncio
import httpx
from loguru import logger
from common import common
from retry import retry
import random
import time

# 配置常量
url = "https://www.douyin.com/aweme/v1/web/comment/list/"

@retry(tries=3, delay=2)
async def fetch_comments(aweme_id: str, cookie: str, cursor: str = "0", count: str = "100"):
    """获取评论数据"""
    try:
        if not cookie:
            raise ValueError("Cookie不能为空")
            
        if not aweme_id:
            raise ValueError("视频ID不能为空")
            
        params = {
            "aweme_id": aweme_id,
            "cursor": cursor,
            "count": count,
            "item_type": 0
        }
        headers = {"cookie": cookie}
        
        # 使用common模块处理参数
        try:
            params, headers = common(url, params, headers)
        except Exception as e:
            logger.error(f"处理请求参数时出错: {str(e)}")
            raise ValueError(f"签名生成失败: {str(e)}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ValueError("视频不存在或已被删除")
                elif e.response.status_code == 403:
                    raise ValueError("访问被拒绝，请检查Cookie是否有效")
                else:
                    raise ValueError(f"HTTP请求失败: {e.response.status_code}")
            
            try:
                data = response.json()
            except Exception as e:
                logger.error(f"解析响应数据失败: {str(e)}")
                logger.error(f"响应内容: {response.text[:200]}")  # 只记录前200个字符
                raise ValueError("返回数据格式错误")
            
            if not isinstance(data, dict):
                logger.error(f"返回数据格式错误: {data}")
                return [], 0, cursor, 0
                
            if data.get("status_code") != 0:
                error_msg = data.get('status_msg', '未知错误')
                logger.error(f"请求失败: {error_msg}")
                if "登录" in error_msg:
                    raise ValueError("Cookie已失效，请更新Cookie")
                elif "禁止访问" in error_msg:
                    raise ValueError("IP被限制，请稍后再试")
                elif "不存在" in error_msg:
                    raise ValueError("视频不存在或已被删除")
                raise ValueError(f"请求失败: {error_msg}")
            
            comments = data.get("comments", [])
            if comments is None:
                comments = []
                
            has_more = data.get("has_more", 0)
            next_cursor = data.get("cursor", cursor)
            total = data.get("total", 0)  # 获取总评论数
            
            # 验证数据类型
            if not isinstance(comments, list):
                logger.error(f"评论数据格式错误: {comments}")
                comments = []
                
            if not isinstance(has_more, (int, bool)):
                logger.error(f"has_more格式错误: {has_more}")
                has_more = 0
                
            if not isinstance(next_cursor, (str, int)):
                logger.error(f"cursor格式错误: {next_cursor}")
                next_cursor = cursor
                
            if not isinstance(total, int):
                logger.error(f"total格式错误: {total}")
                total = 0
                
            return comments, has_more, str(next_cursor), total
            
    except ValueError as e:
        logger.error(f"获取评论失败: {str(e)}")
        raise
    except httpx.HTTPError as e:
        logger.error(f"网络请求失败: {str(e)}")
        raise ValueError(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"获取评论时发生未知错误: {str(e)}")
        raise ValueError(f"获取评论失败: {str(e)}")

async def check_comments_count(aweme_id: str, cookie: str) -> int:
    """检查视频的总评论数"""
    try:
        comments, _, _, total = await fetch_comments(aweme_id, cookie, "0", "1")
        if total == 0 and comments:
            # 如果返回的total为0但实际有评论，使用评论列表长度
            return len(comments)
        return total
    except Exception as e:
        logger.error(f"检查评论数量时发生错误: {str(e)}")
        raise  # 向上传递错误，让调用者处理

async def fetch_all_comments(aweme_id: str, cookie: str, use_batch_mode: bool = None):
    """获取所有评论"""
    try:
        # 如果未指定模式，先检查评论总数
        if use_batch_mode is None:
            try:
                total_comments = await check_comments_count(aweme_id, cookie)
                use_batch_mode = total_comments > 1000  # 超过1000条评论使用批量模式
                logger.info(f"检测到总评论数: {total_comments}，{'使用' if use_batch_mode else '不使用'}批量模式")
            except Exception as e:
                logger.warning(f"检查评论数量失败: {str(e)}，将使用默认模式")
                use_batch_mode = False
        
        cursor = "0"
        all_comments = []
        has_more = 1
        retry_count = 0
        max_retries = 5
        last_cursor = None
        empty_page_count = 0
        max_empty_pages = 5
        last_comment_count = 0
        no_progress_count = 0
        max_no_progress = 3
        
        # 批量模式参数调整
        if use_batch_mode:
            count = "30"  # 减小每页评论数，提高稳定性
            min_delay = 1.5  # 增加延迟，避免请求过快
            max_delay = 2.5
            max_retries = 8  # 增加重试次数
            max_empty_pages = 8  # 增加空页面容忍度
        else:
            count = "20"
            min_delay = 2
            max_delay = 3
            max_retries = 5
            max_empty_pages = 5
        
        # 记录起始时间和上次进度更新时间
        start_time = time.time()
        last_progress_time = start_time
        progress_interval = 30  # 每30秒显示一次进度
        
        while has_more and retry_count < max_retries and empty_page_count < max_empty_pages:
            try:
                # 定期显示采集进度
                current_time = time.time()
                if current_time - last_progress_time >= progress_interval:
                    elapsed_time = current_time - start_time
                    rate = len(all_comments) / elapsed_time if elapsed_time > 0 else 0
                    logger.info(f"采集进度 - 已获取: {len(all_comments)} 条评论, 速率: {rate:.2f} 条/秒")
                    last_progress_time = current_time
                
                if cursor == last_cursor:
                    logger.warning(f"检测到重复的cursor值: {cursor}，尝试跳过")
                    # 使用评论数来计算下一个cursor
                    next_cursor_val = int(cursor) + int(count)
                    if next_cursor_val <= len(all_comments):
                        cursor = str(next_cursor_val)
                    else:
                        # 如果计算的cursor超过了已有评论数，尝试更小的增量
                        cursor = str(int(cursor) + int(int(count) / 2))
                        logger.warning(f"使用更小的增量调整cursor: {cursor}")
                
                comments, has_more, next_cursor, _ = await fetch_comments(aweme_id, cookie, cursor, count)
                
                if not comments and has_more:
                    empty_page_count += 1
                    retry_count += 1
                    logger.warning(f"未获取到评论但has_more为真，第{retry_count}次重试，连续空页面次数：{empty_page_count}")
                    if empty_page_count >= max_empty_pages:
                        logger.warning("连续多次未获取到评论，可能已到达末尾")
                        break
                    await asyncio.sleep(random.uniform(2, 3))  # 空页面时增加等待时间
                    continue
                
                if comments:
                    empty_page_count = 0
                    
                    # 检查新评论是否与已有评论重复
                    new_comment_ids = set(comment["cid"] for comment in comments if isinstance(comment, dict) and "cid" in comment)
                    existing_comment_ids = set(comment["cid"] for comment in all_comments if isinstance(comment, dict) and "cid" in comment)
                    unique_comments = [c for c in comments if isinstance(c, dict) and "cid" in c and c["cid"] not in existing_comment_ids]
                    
                    if unique_comments:
                        all_comments.extend(unique_comments)
                        logger.info(f"已获取 {len(all_comments)} 条评论")
                        retry_count = 0  # 获取到新评论时重置重试计数
                        no_progress_count = 0
                    else:
                        logger.warning("本页评论全部重复，可能存在分页问题")
                        no_progress_count += 1
                        if no_progress_count >= max_no_progress:
                            logger.warning(f"连续 {max_no_progress} 次未获取到新评论，尝试调整cursor")
                            # 尝试更小的跳转步长
                            cursor = str(int(cursor) + int(int(count) / 2))
                            no_progress_count = 0
                            continue
                
                # 检查是否有实际进展
                if len(all_comments) == last_comment_count:
                    no_progress_count += 1
                else:
                    no_progress_count = 0
                    last_comment_count = len(all_comments)
                
                # 更新cursor
                last_cursor = cursor
                if next_cursor == "0" or int(next_cursor) < int(cursor):
                    # cursor异常，使用更保守的递增策略
                    cursor = str(int(cursor) + int(int(count) / 2))
                    logger.warning(f"cursor异常，使用保守递增: {cursor}")
                else:
                    cursor = next_cursor
                
                # 根据当前进展调整延迟
                if no_progress_count > 0:
                    # 如果没有新评论，增加延迟
                    await asyncio.sleep(random.uniform(max_delay, max_delay + 1))
                else:
                    # 正常延迟
                    await asyncio.sleep(random.uniform(min_delay, max_delay))
                
            except ValueError as e:
                if "Cookie已失效" in str(e) or "视频不存在" in str(e):
                    raise  # 这些错误直接抛出
                retry_count += 1
                logger.warning(f"获取评论出错: {str(e)}，第{retry_count}次重试")
                await asyncio.sleep(random.uniform(2, 3))
            except Exception as e:
                retry_count += 1
                logger.error(f"获取评论时发生错误: {str(e)}，第{retry_count}次重试")
                await asyncio.sleep(random.uniform(2, 3))
        
        if not all_comments:
            if retry_count >= max_retries:
                raise ValueError("达到最大重试次数，未能获取到评论")
            elif empty_page_count >= max_empty_pages:
                raise ValueError("连续多次未获取到评论，请检查视频是否有评论")
            else:
                raise ValueError("未获取到任何评论，请检查视频ID是否正确")
        
        # 显示最终统计信息
        total_time = time.time() - start_time
        rate = len(all_comments) / total_time if total_time > 0 else 0
        logger.info(f"评论采集完成，共获取 {len(all_comments)} 条评论，用时 {total_time:.2f} 秒，平均速率 {rate:.2f} 条/秒")
        return all_comments
        
    except Exception as e:
        logger.error(f"获取所有评论时发生错误: {str(e)}")
        raise
