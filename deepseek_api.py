import requests
import json
import os
from typing import Optional

class DeepSeekAPI:
    """DeepSeek API 处理类"""
    
    def __init__(self):
        self.api_key_file = "deepseek_api_key.txt"
        self.base_url = "https://api.deepseek.com/v1"
        self.api_key = self._load_api_key()

    def _load_api_key(self) -> Optional[str]:
        """从文件加载API Key"""
        try:
            if os.path.exists(self.api_key_file):
                with open(self.api_key_file, "r") as f:
                    return f.read().strip()
            return None
        except Exception:
            return None

    def save_api_key(self, api_key: str) -> bool:
        """保存API Key到文件"""
        try:
            with open(self.api_key_file, "w") as f:
                f.write(api_key)
            self.api_key = api_key
            return True
        except Exception:
            return False

    def verify_api_key(self, api_key: str) -> bool:
        """验证API Key是否有效"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        try:
            # 发送一个简单的测试请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10
                }
            )
            return response.status_code == 200
        except Exception:
            return False

    def analyze_comments(self, comments_text: str) -> dict:
        """分析评论内容"""
        if not self.api_key:
            raise ValueError("API Key未设置")

        prompt = f"""请分析以下抖音评论内容，并提供以下方面的分析：
1. 情感倾向分析（正面、负面、中性的比例）
2. 主要话题和关键词提取
3. 用户意见和建议的总结
4. 热点问题或争议点
5. 建议的回应策略

评论内容：
{comments_text}
"""
        return self._send_request(prompt)

    def analyze_with_prompt(self, prompt: str) -> dict:
        """使用自定义提示词分析内容"""
        if not self.api_key:
            raise ValueError("API Key未设置")
        return self._send_request(prompt)

    def _send_request(self, prompt: str) -> dict:
        """发送API请求"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            raise ValueError(f"分析评论失败: {str(e)}") 