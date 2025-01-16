import sys
import time
import threading
from PyQt6.QtWidgets import QApplication, QMessageBox
from login_window import LoginWindow
import requests
from loguru import logger

def verify_token(token):
    """验证token是否有效"""
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(
            "https://xxzcqrmtfyhm.sealoshzh.site/api/users/me",
            headers=headers
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"验证token时发生错误: {str(e)}")
        return False

def simulate_second_login(username, password, first_token, delay=5):
    """模拟第二个用户使用相同账号登录"""
    logger.info("等待第一个用户登录成功...")
    time.sleep(delay)
    
    try:
        # 验证第一个用户的token是否还有效
        logger.info("验证第一个用户的token...")
        if verify_token(first_token):
            logger.info("第一个用户的token仍然有效")
        else:
            logger.warning("第一个用户的token已失效")
        
        # 模拟第二个用户登录
        logger.info("尝试第二个用户登录...")
        response = requests.post(
            "https://xxzcqrmtfyhm.sealoshzh.site/api/login",
            json={
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            second_token = data.get("token")
            logger.info("第二个用户登录成功")
            
            # 再次验证第一个用户的token
            time.sleep(2)  # 等待一下让服务器处理
            logger.info("再次验证第一个用户的token...")
            if verify_token(first_token):
                logger.warning("警告：第一个用户的token仍然有效，互斥登录可能未生效")
            else:
                logger.info("成功：第一个用户的token已失效，互斥登录生效")
        else:
            logger.error(f"第二个用户登录失败: {response.status_code}")
            
    except Exception as e:
        logger.error(f"模拟第二次登录时发生错误: {str(e)}")

def test_concurrent_login():
    """测试并发登录场景"""
    app = QApplication(sys.argv)
    
    # 测试账号信息
    username = "admin"
    password = "admin123"
    
    # 创建并显示第一个登录窗口
    logger.info("开始测试：创建第一个登录窗口")
    login_window = LoginWindow()
    login_window.show()
    
    # 自动填充登录信息
    login_window.username_input.setText(username)
    login_window.password_input.setText(password)
    login_window.login()
    
    # 等待登录成功
    while login_window.isVisible():
        app.processEvents()
    
    first_token = login_window.get_token()
    if not first_token:
        logger.error("第一个用户登录失败")
        return 1
    
    logger.info("第一个用户登录成功")
    
    # 创建线程模拟第二个用户登录
    second_login_thread = threading.Thread(
        target=simulate_second_login,
        args=(username, password, first_token)
    )
    second_login_thread.start()
    
    # 运行应用，等待被踢出
    return app.exec()

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    logger.info("开始互斥登录测试...")
    sys.exit(test_concurrent_login()) 