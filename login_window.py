import sys
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from loguru import logger

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音评论采集工具 - 登录")
        self.setGeometry(100, 100, 400, 250)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 添加标题标签
        title_label = QLabel("抖音评论采集工具")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 添加说明标签
        info_label = QLabel("请输入账号密码登录")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 用户名输入框
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setStyleSheet("padding: 5px; margin: 5px;")
        layout.addWidget(self.username_input)
        
        # 密码输入框
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 5px; margin: 5px;")
        layout.addWidget(self.password_input)
        
        # 登录按钮
        login_button = QPushButton("登录")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                margin: 10px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        # 设置布局
        central_widget.setLayout(layout)
        
        # 存储用户信息和token
        self.token = None
        self.user_info = None
        
        # API基础URL
        self.base_url = "https://xxzcqrmtfyhm.sealoshzh.site/api"
        
    def login(self):
        """处理登录请求"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "错误", "请输入用户名和密码")
            return
            
        try:
            self.status_label.setText("正在登录...")
            self.status_label.setStyleSheet("color: blue;")
            
            response = requests.post(
                f"{self.base_url}/login",
                json={
                    "username": username,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.token = data["token"]
                    self.user_info = data["user"]
                    
                    self.status_label.setText("登录成功")
                    self.status_label.setStyleSheet("color: green;")
                    self.accept_login()
                else:
                    self.status_label.setText("登录失败")
                    self.status_label.setStyleSheet("color: red;")
                    QMessageBox.warning(self, "登录失败", data.get("message", "账号或密码错误"))
                    self.password_input.clear()
                    self.password_input.setFocus()
            else:
                self.status_label.setText("服务器错误")
                self.status_label.setStyleSheet("color: red;")
                QMessageBox.warning(self, "登录失败", "服务器连接失败")
                
        except Exception as e:
            self.status_label.setText("连接错误")
            self.status_label.setStyleSheet("color: red;")
            logger.error(f"登录时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"登录时发生错误: {str(e)}")
            
    def accept_login(self):
        """登录成功的处理"""
        if self.token and self.user_info:
            self.hide()
        else:
            # 如果没有token或用户信息，说明登录未成功
            QMessageBox.critical(self, "登录失败", "登录验证失败，请重试")
            self.password_input.clear()
            self.password_input.setFocus()
        
    def get_token(self):
        """获取当前token"""
        return self.token
        
    def get_user_info(self):
        """获取用户信息"""
        return self.user_info
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果未登录成功就关闭窗口，则退出程序
        if not self.token or not self.user_info:
            QApplication.quit()
        event.accept() 