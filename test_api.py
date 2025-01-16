import requests
import json
from loguru import logger

class APITester:
    def __init__(self):
        self.base_url = "https://xxzcqrmtfyhm.sealoshzh.site/api"
        self.token = None
        self.test_credentials = {
            "username": "admin",
            "password": "admin123"
        }
        
    def test_login(self):
        """测试登录API"""
        print("\n=== 测试登录API ===")
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json=self.test_credentials
            )
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.token = data["token"]
                    print("✅ 登录API测试成功")
                    return True
            print("❌ 登录API测试失败")
            return False
        except Exception as e:
            print(f"❌ 登录API测试出错: {str(e)}")
            return False
            
    def test_user_info(self):
        """测试获取用户信息API"""
        print("\n=== 测试用户信息API ===")
        if not self.token:
            print("❌ 未登录，无法测试")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            response = requests.get(
                f"{self.base_url}/users/1",
                headers=headers
            )
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                print("✅ 用户信息API测试成功")
                return True
            print("❌ 用户信息API测试失败")
            return False
        except Exception as e:
            print(f"❌ 用户信息API测试出错: {str(e)}")
            return False
            
    def test_logout(self):
        """测试登出API"""
        print("\n=== 测试登出API ===")
        if not self.token:
            print("❌ 未登录，无法测试")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            response = requests.post(
                f"{self.base_url}/logout",
                headers=headers
            )
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                print("✅ 登出API测试成功")
                return True
            print("❌ 登出API测试失败")
            return False
        except Exception as e:
            print(f"❌ 登出API测试出错: {str(e)}")
            return False
            
    def run_all_tests(self):
        """运行所有测试"""
        print("开始API连接测试...\n")
        
        # 测试服务器连接
        try:
            response = requests.get(self.base_url)
            print(f"服务器连接测试 - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 服务器连接失败: {str(e)}")
            return
            
        # 运行所有API测试
        tests = [
            self.test_login,
            self.test_user_info,
            self.test_logout
        ]
        
        results = []
        for test in tests:
            result = test()
            results.append(result)
            
        # 打印测试总结
        print("\n=== 测试总结 ===")
        total = len(results)
        passed = sum(1 for r in results if r)
        print(f"总计测试: {total}")
        print(f"通过测试: {passed}")
        print(f"失败测试: {total - passed}")
        
if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests() 