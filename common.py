import requests
import execjs
import urllib.parse
import re
import random
import cookiesparser
import platform
from loguru import logger
from typing import Optional, Dict, Tuple
from retry import retry

# 常量定义
HOST = 'https://www.douyin.com'

# 通用请求参数
COMMON_PARAMS = {
    'device_platform': 'webapp',
    'aid': '6383',
    'channel': 'channel_pc_web',
    'update_version_code': '170400',
    'pc_client_type': '1',  # Windows
    'version_code': '190500',
    'version_name': '19.5.0',
    'cookie_enabled': 'true',
    'screen_width': '2560',  # from cookie dy_swidth
    'screen_height': '1440',  # from cookie dy_sheight
    'browser_language': 'zh-CN',
    'browser_platform': 'Win32',
    'browser_name': 'Chrome',
    'browser_version': '126.0.0.0',
    'browser_online': 'true',
    'engine_name': 'Blink',
    'engine_version': '126.0.0.0',
    'os_name': 'Windows',
    'os_version': '10',
    'cpu_core_num': '24',  # device_web_cpu_core
    'device_memory': '8',  # device_web_memory_size
    'platform': 'PC',
    'downlink': '10',
    'effective_type': '4g',
    'round_trip_time': '50',
}

# 通用请求头
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "sec-ch-ua-platform": "Windows",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "referer": "https://www.douyin.com/?recommend=1",
    "priority": "u=1, i",
    "pragma": "no-cache",
    "cache-control": "no-cache",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
    "accept": "application/json, text/plain, */*",
    "dnt": "1",
}

# 根据操作系统选择不同的Node.js运行时配置
if platform.system() == 'Windows':
    node_path = r'C:\Program Files\nodejs\node.exe'  # Windows默认Node.js路径
    execjs.register('Node', {'runtime_path': node_path})
else:
    node_path = '/usr/local/bin/node'  # Mac默认Node.js路径
    execjs.register('Node', {'runtime_path': node_path})

try:
    # 加载签名脚本
    with open('douyin.js', 'r', encoding='utf-8') as f:
        js_code = f.read()
        # 处理可能的编码问题
        js_code = js_code.replace('\ufeff', '')  # 移除BOM
        js_code = js_code.encode('utf-8').decode('utf-8-sig')  # 处理编码
    DOUYIN_SIGN = execjs.compile(js_code)
    logger.success("成功加载签名脚本")
except Exception as e:
    logger.error(f"加载签名脚本失败: {str(e)}")
    raise

@retry(tries=3, delay=2)
def get_webid(headers: Dict) -> Optional[str]:
    """
    获取用户唯一标识webid
    
    Args:
        headers: 请求头信息
        
    Returns:
        str: 成功返回webid，失败返回None
        
    Raises:
        requests.RequestException: 请求失败时抛出
    """
    try:
        url = 'https://www.douyin.com/?recommend=1'
        headers['sec-fetch-dest'] = 'document'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200 or not response.text:
            logger.warning(f"获取webid失败: HTTP {response.status_code}")
            return None
            
        pattern = r'\\"user_unique_id\\":\\"(\d+)\\"'
        match = re.search(pattern, response.text)
        if match:
            webid = match.group(1)
            logger.debug(f"成功获取webid: {webid}")
            return webid
            
        logger.warning("未找到webid")
        return None
        
    except requests.RequestException as e:
        logger.error(f"请求webid时发生错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"获取webid时发生未知错误: {str(e)}")
        return None

def deal_params(params: Dict, headers: Dict) -> Dict:
    """
    处理请求参数，添加必要的认证信息
    
    Args:
        params: 原始请求参数
        headers: 请求头信息
        
    Returns:
        Dict: 处理后的请求参数
    """
    try:
        cookie = headers.get('cookie') or headers.get('Cookie')
        if not cookie:
            logger.warning("未找到cookie信息")
            return params
            
        cookie_dict = cookiesparser.parse(cookie)
        params['msToken'] = get_ms_token()
        params['screen_width'] = cookie_dict.get('dy_swidth', 2560)
        params['screen_height'] = cookie_dict.get('dy_sheight', 1440)
        params['cpu_core_num'] = cookie_dict.get('device_web_cpu_core', 24)
        params['device_memory'] = cookie_dict.get('device_web_memory_size', 8)
        params['verifyFp'] = cookie_dict.get('s_v_web_id', None)
        params['fp'] = cookie_dict.get('s_v_web_id', None)
        params['webid'] = get_webid(headers)
        
        return params
        
    except Exception as e:
        logger.error(f"处理请求参数时发生错误: {str(e)}")
        return params

def get_ms_token(randomlength: int = 120) -> str:
    """
    生成随机msToken
    
    Args:
        randomlength: 生成的随机字符串长度
        
    Returns:
        str: 随机生成的msToken
    """
    try:
        base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789='
        length = len(base_str) - 1
        random_str = ''.join(base_str[random.randint(0, length)] for _ in range(randomlength))
        return random_str
    except Exception as e:
        logger.error(f"生成msToken时发生错误: {str(e)}")
        return 'default_token'  # 返回默认token而不是失败

def get_webid(params=None):
    """生成19位随机数字的webid"""
    try:
        webid = ''.join([str(random.randint(0, 9)) for _ in range(19)])
        return webid
    except Exception as e:
        logger.error(f"生成webid时出错: {str(e)}")
        return '7362810250930783783'  # 返回一个默认的webid

def common(uri: str, params: Dict, headers: Dict) -> Tuple[Dict, Dict]:
    """
    处理通用请求参数和头信息
    
    Args:
        uri: 请求URI
        params: 请求参数
        headers: 请求头
        
    Returns:
        Tuple[Dict, Dict]: 处理后的参数和头信息
        
    Raises:
        Exception: 处理过程中的错误
    """
    try:
        # 更新通用参数和头信息
        params.update(COMMON_PARAMS)
        headers.update(COMMON_HEADERS)
        
        # 添加webid
        if 'webid' not in params:
            params['webid'] = get_webid(params)
            
        # 处理参数
        params = deal_params(params, headers)
        
        # 生成签名
        try:
            # 构建查询字符串
            query_items = []
            for k, v in sorted(params.items()):  # 对参数排序以保证一致性
                if v is not None:
                    encoded_value = urllib.parse.quote(str(v))
                    query_items.append(f'{k}={encoded_value}')
            query = '&'.join(query_items)
            
            # 根据URI选择签名函数
            call_name = 'sign_reply' if 'reply' in uri else 'sign_datail'
            
            try:
                # 生成签名
                a_bogus = DOUYIN_SIGN.call(call_name, query, headers["User-Agent"])
                if not a_bogus:
                    raise ValueError("签名生成结果为空")
                    
                params["X-Bogus"] = a_bogus
                logger.debug(f"成功生成签名: {a_bogus[:20]}...")
                
            except execjs.RuntimeError as e:
                logger.error(f"JavaScript运行时错误: {str(e)}")
                raise ValueError(f"签名生成失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"生成签名时发生错误: {str(e)}")
            raise
            
        return params, headers
        
    except Exception as e:
        logger.error(f"处理请求信息时发生错误: {str(e)}")
        raise
