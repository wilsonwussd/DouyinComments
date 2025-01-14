import sys
import os
import asyncio
import pandas as pd
import traceback
import re
import requests
import json
from urllib.parse import urlparse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QCheckBox, QProgressBar, QMessageBox, QHeaderView,
    QTextEdit, QRadioButton, QButtonGroup, QTabWidget, QStatusBar,
    QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
from main import fetch_all_comments_async, fetch_all_replies_async, process_comments, process_replies, load_cookie
from deepseek_api import DeepSeekAPI
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    "gui_error.log",
    rotation="500 MB",
    level="ERROR",
    backtrace=True,
    diagnose=True
)

class CommentWorker(QThread):
    """后台工作线程，用于获取评论数据"""
    finished = pyqtSignal(object)  # 完成信号
    progress = pyqtSignal(int)     # 进度信号
    error = pyqtSignal(str)        # 错误信号
    log = pyqtSignal(str)          # 日志信号

    def __init__(self, aweme_id, get_replies=False, cookie=None):
        super().__init__()
        self.aweme_id = aweme_id
        self.get_replies = get_replies
        self.cookie = cookie
        
    def run(self):
        try:
            self.log.emit("开始创建事件循环...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 使用传入的cookie
            if self.cookie:
                os.environ["DOUYIN_COOKIE"] = self.cookie
            
            self.log.emit(f"开始获取视频 {self.aweme_id} 的评论...")
            try:
                comments = loop.run_until_complete(fetch_all_comments_async(self.aweme_id))
                if not comments:
                    raise Exception("未获取到评论数据")
            except ValueError as e:
                error_msg = str(e)
                if "Cookie已失效" in error_msg:
                    raise Exception("Cookie已失效，请更新Cookie")
                elif "视频不存在" in error_msg or "已被删除" in error_msg:
                    raise Exception("视频不存在或已被删除")
                elif "IP被限制" in error_msg:
                    raise Exception("IP被限制，请稍后再试")
                else:
                    raise Exception(f"获取评论失败: {error_msg}")
                
            self.log.emit("处理评论数据...")
            comments_df = process_comments(comments)
            self.log.emit(f"成功获取 {len(comments)} 条评论")
            
            if self.get_replies:
                self.log.emit("开始获取评论回复...")
                try:
                    replies = loop.run_until_complete(fetch_all_replies_async(comments))
                    self.log.emit(f"成功获取 {len(replies)} 条回复")
                    replies_df = process_replies(replies, comments_df)
                    result = pd.concat([comments_df, replies_df], ignore_index=True)
                except Exception as e:
                    self.log.emit(f"获取回复时出错: {str(e)}")
                    # 如果获取回复失败，仍然返回评论数据
                    result = comments_df
            else:
                result = comments_df
                
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"错误详情: {error_msg}")
            self.error.emit(error_msg)
        finally:
            try:
                loop.close()
                self.log.emit("事件循环已关闭")
            except Exception as e:
                logger.error(f"关闭事件循环时出错: {str(e)}")

def extract_video_id(share_text):
    """从分享文本中提取视频ID"""
    try:
        # 尝试直接匹配数字ID
        if share_text.isdigit():
            return share_text
            
        # 匹配短链接
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|v\.douyin\.com/[^\s<>"]+'
        urls = re.findall(url_pattern, share_text)
        
        if not urls:
            return None
            
        # 获取第一个URL
        url = urls[0]
        
        # 如果是短链接，获取重定向后的URL
        if 'v.douyin.com' in url:
            response = requests.get(url, allow_redirects=True)
            url = response.url
            
        # 从URL中提取视频ID
        video_id_pattern = r'/video/(\d+)'
        match = re.search(video_id_pattern, url)
        
        if match:
            return match.group(1)
            
        return None
    except Exception as e:
        logger.error(f"解析分享链接时出错: {str(e)}")
        return None

class CookieManager:
    """Cookie管理类"""
    def __init__(self):
        self.cookie_file = "cookie.txt"
        self.cookie_json_file = "cookie_json.txt"
        
    def save_cookies(self, cookies_json):
        """保存Cookies"""
        try:
            # 保存原始JSON格式的cookies
            with open(self.cookie_json_file, "w", encoding="utf-8") as f:
                f.write(cookies_json)
            
            # 解析JSON格式的cookies并保存为字符串格式
            cookies_data = json.loads(cookies_json)
            cookie_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies_data])
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                f.write(cookie_str)
            return True, "Cookies保存成功"
        except Exception as e:
            return False, f"保存Cookies失败: {str(e)}"
            
    def load_cookies(self):
        """加载Cookies字符串格式"""
        try:
            if not os.path.exists(self.cookie_file):
                return False, "Cookie文件不存在"
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                return True, f.read()
        except Exception as e:
            return False, f"加载Cookies失败: {str(e)}"
            
    def load_cookies_json(self):
        """加载JSON格式的Cookies"""
        try:
            if not os.path.exists(self.cookie_json_file):
                return False, "Cookie JSON文件不存在"
            with open(self.cookie_json_file, "r", encoding="utf-8") as f:
                return True, f.read()
        except Exception as e:
            return False, f"加载Cookies JSON失败: {str(e)}"
            
    def verify_cookies(self, cookies):
        """验证Cookies有效性"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Cookie": cookies
            }
            # 尝试访问抖音首页
            response = requests.get("https://www.douyin.com", headers=headers)
            return response.status_code == 200, "Cookies有效" if response.status_code == 200 else "Cookies无效"
        except Exception as e:
            return False, f"验证Cookies失败: {str(e)}"

class AIAnalysisWorker(QThread):
    """AI分析工作线程"""
    finished = pyqtSignal(str)  # 完成信号
    error = pyqtSignal(str)    # 错误信号

    def __init__(self, api: DeepSeekAPI, comments_text: str, custom_prompt: str = None):
        super().__init__()
        self.api = api
        self.comments_text = comments_text
        self.custom_prompt = custom_prompt

    def run(self):
        try:
            if self.custom_prompt:
                # 使用自定义提示词
                result = self.api.analyze_with_prompt(self.custom_prompt)
            else:
                # 使用默认分析
                result = self.api.analyze_comments(self.comments_text)
            
            # 提取AI回复内容
            response_text = result['choices'][0]['message']['content']
            self.finished.emit(response_text)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音评论采集工具")
        
        # 设置合适的字体
        font = QFont()
        if sys.platform == "darwin":  # macOS
            font.setFamily("Helvetica")  # 使用更基础的系统字体
            chinese_font = QFont()
            chinese_font.setFamily("STHeiti")  # macOS自带的中文字体
            QApplication.setFont(chinese_font, "QWidget")
        else:
            font.setFamily("Microsoft YaHei")  # Windows 默认中文字体
        font.setPointSize(12)
        QApplication.setFont(font)
        
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化Cookie管理器
        self.cookie_manager = CookieManager()
        self.current_cookie = None
        
        # 创建定时器，每5分钟验证一次Cookie
        self.cookie_timer = QTimer()
        self.cookie_timer.setInterval(5 * 60 * 1000)  # 5分钟 = 5 * 60 * 1000毫秒
        self.cookie_timer.timeout.connect(self.auto_verify_cookies)
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 创建状态标签
        self.status_layout = QHBoxLayout()
        
        # Cookie导入状态
        self.cookie_import_label = QLabel("Cookie导入状态:")
        self.cookie_import_icon = QLabel("●")
        self.cookie_import_icon.setStyleSheet("color: black;")
        self.cookie_import_text = QLabel("未导入")
        
        # Cookie验证状态
        self.cookie_verify_label = QLabel("Cookie验证状态:")
        self.cookie_verify_icon = QLabel("●")
        self.cookie_verify_icon.setStyleSheet("color: black;")
        self.cookie_verify_text = QLabel("未验证")
        
        # 将标签添加到状态栏
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加导入状态
        status_layout.addWidget(self.cookie_import_label)
        status_layout.addWidget(self.cookie_import_icon)
        status_layout.addWidget(self.cookie_import_text)
        status_layout.addSpacing(20)  # 添加间距
        
        # 添加验证状态
        status_layout.addWidget(self.cookie_verify_label)
        status_layout.addWidget(self.cookie_verify_icon)
        status_layout.addWidget(self.cookie_verify_text)
        status_layout.addStretch()
        
        self.statusBar.addWidget(status_widget)
        
        # 初始化DeepSeek API
        self.deepseek_api = DeepSeekAPI()
        
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 创建三个标签页（按新的顺序）
        self.create_cookie_tab()      # 第一个标签页：Cookie管理
        self.create_collection_tab()  # 第二个标签页：评论采集
        self.create_ai_analysis_tab() # 第三个标签页：AI分析
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        self.central_widget.setLayout(main_layout)
        
        # 初始化工作线程
        self.worker = None
        
        # 添加日志
        self.add_log("程序已启动，请先在Cookie管理页面导入并验证Cookie...")

    def add_log(self, message):
        """添加日志到显示区域"""
        self.log_display.append(f"{message}")
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def start_collection(self):
        """开始采集评论"""
        try:
            # 检查是否有cookie
            if not self.current_cookie:
                QMessageBox.warning(self, "警告", "请先在Cookie管理页面导入并验证Cookie")
                return
                
            # 在开始采集前重新验证cookie
            valid, message = self.cookie_manager.verify_cookies(self.current_cookie)
            if not valid:
                self.current_cookie = None
                self.cookie_verify_icon.setStyleSheet("color: red;")
                self.cookie_verify_text.setText("无效")
                QMessageBox.warning(self, "Cookie已失效", "Cookie已失效，请重新导入并验证Cookie")
                return
                
            input_text = self.input_field.text().strip()
            if not input_text:
                QMessageBox.warning(self, "警告", "请粘贴抖音分享链接")
                return
            
            # 解析分享链接
            self.add_log("正在解析分享链接...")
            video_id = extract_video_id(input_text)
            if not video_id:
                QMessageBox.warning(self, "警告", "无法从分享链接中提取视频ID")
                return
            self.add_log(f"成功提取视频ID: {video_id}")
            
            # 清空日志显示和表格
            self.log_display.clear()
            self.table.setRowCount(0)
            self.add_log(f"开始采集视频ID: {video_id} 的评论...")
            
            # 禁用开始按钮和保存按钮
            self.start_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 显示忙碌状态
            
            # 创建并启动工作线程，传入当前cookie
            self.worker = CommentWorker(video_id, self.get_replies_checkbox.isChecked(), self.current_cookie)
            self.worker.finished.connect(self.on_collection_finished)
            self.worker.error.connect(self.on_collection_error)
            self.worker.log.connect(self.add_log)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动采集时出错: {str(e)}")
            self.start_button.setEnabled(True)
            self.progress_bar.setVisible(False)

    def on_collection_error(self, error_msg):
        """处理采集错误"""
        self.start_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.save_button.setEnabled(False)
        
        # 根据错误类型显示不同的提示
        if "Cookie已失效" in error_msg:
            QMessageBox.warning(self, "Cookie已失效", "Cookie已失效，请更新Cookie")
            self.cookie_verify_icon.setStyleSheet("color: red;")
            self.cookie_verify_text.setText("无效")
        elif "视频不存在" in error_msg or "已被删除" in error_msg:
            QMessageBox.warning(self, "视频不存在", "视频不存在或已被删除")
        elif "IP被限制" in error_msg:
            QMessageBox.warning(self, "访问受限", "IP被限制，请稍后再试")
        else:
            QMessageBox.critical(self, "错误", f"采集失败: {error_msg}")
        
        self.add_log(f"采集失败: {error_msg}")

    def on_collection_finished(self, data):
        """采集完成的回调函数"""
        try:
            if data is None or data.empty:
                self.add_log("未获取到有效数据")
                QMessageBox.warning(self, "提示", "未获取到有效数据")
                return
                
            # 清空表格
            self.table.setRowCount(0)
            
            # 保存数据用于导出
            self.current_data = data
            
            # 填充数据
            for index, row in data.iterrows():
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                
                # 设置单元格内容
                self.table.setItem(row_position, 0, QTableWidgetItem(str(row['评论ID'])))
                self.table.setItem(row_position, 1, QTableWidgetItem(str(row['评论内容'])))
                self.table.setItem(row_position, 2, QTableWidgetItem(str(row['点赞数'])))
                self.table.setItem(row_position, 3, QTableWidgetItem(str(row['评论时间'])))
                self.table.setItem(row_position, 4, QTableWidgetItem(str(row['用户昵称'])))
                self.table.setItem(row_position, 5, QTableWidgetItem(str(row['用户抖音号'])))
                self.table.setItem(row_position, 6, QTableWidgetItem(str(row['ip归属'])))
                self.table.setItem(row_position, 7, QTableWidgetItem(str(row.get('回复总数', 0))))
            
            # 恢复界面状态
            self.start_button.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.save_button.setEnabled(True)
            
            # 添加日志
            self.add_log(f"数据采集完成，共获取 {self.table.rowCount()} 条数据")
            
            # 显示完成消息
            QMessageBox.information(self, "提示", f"采集完成，共获取 {self.table.rowCount()} 条数据")
            
        except Exception as e:
            self.add_log(f"处理数据时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理数据时出错: {str(e)}")
            self.start_button.setEnabled(True)
            self.progress_bar.setVisible(False)

    def load_saved_cookies(self):
        """加载保存的Cookies，静默验证不显示提示框"""
        success, cookies_json = self.cookie_manager.load_cookies_json()
        if success:
            self.cookie_input.setText(cookies_json)
            # 加载Cookie字符串格式并设置状态
            success, cookies = self.cookie_manager.load_cookies()
            if success:
                self.cookie_import_icon.setStyleSheet("color: green;")
                self.cookie_import_text.setText("已导入")
                # 静默验证Cookie
                try:
                    valid, _ = self.cookie_manager.verify_cookies(cookies)
                    if valid:
                        self.current_cookie = cookies
                        self.cookie_verify_icon.setStyleSheet("color: green;")
                        self.cookie_verify_text.setText("有效")
                        # 启动定时验证
                        self.cookie_timer.start()
                    else:
                        self.cookie_verify_icon.setStyleSheet("color: red;")
                        self.cookie_verify_text.setText("无效")
                except:
                    # 验证出错时不显示错误提示，只更新状态
                    self.cookie_verify_icon.setStyleSheet("color: red;")
                    self.cookie_verify_text.setText("无效")
            
    def import_cookies(self):
        """导入Cookies"""
        try:
            cookies_json = self.cookie_input.toPlainText().strip()
            if not cookies_json:
                QMessageBox.warning(self, "警告", "请先粘贴Cookies内容")
                return
                
            success, message = self.cookie_manager.save_cookies(cookies_json)
            if success:
                self.cookie_import_icon.setStyleSheet("color: green;")
                self.cookie_import_text.setText("已导入")
                self.cookie_verify_icon.setStyleSheet("color: black;")
                self.cookie_verify_text.setText("未验证")
                QMessageBox.information(self, "成功", message)
            else:
                self.cookie_import_icon.setStyleSheet("color: red;")
                self.cookie_import_text.setText("导入失败")
                QMessageBox.warning(self, "失败", message)
        except Exception as e:
            self.cookie_import_icon.setStyleSheet("color: red;")
            self.cookie_import_text.setText("导入失败")
            QMessageBox.critical(self, "错误", f"导入Cookies时出错: {str(e)}")
            
    def verify_cookies(self):
        """手动验证Cookies，显示验证结果"""
        try:
            success, cookies = self.cookie_manager.load_cookies()
            if not success:
                self.cookie_import_icon.setStyleSheet("color: red;")
                self.cookie_import_text.setText("加载失败")
                self.cookie_verify_icon.setStyleSheet("color: red;")
                self.cookie_verify_text.setText("无效")
                QMessageBox.warning(self, "警告", cookies)
                return
                
            valid, message = self.cookie_manager.verify_cookies(cookies)
            self.cookie_import_text.setText("已导入")
            
            if valid:
                self.current_cookie = cookies
                self.cookie_verify_icon.setStyleSheet("color: green;")
                self.cookie_verify_text.setText("有效")
                QMessageBox.information(self, "成功", message)
                # 启动定时验证
                self.cookie_timer.start()
            else:
                self.current_cookie = None
                self.cookie_verify_icon.setStyleSheet("color: red;")
                self.cookie_verify_text.setText("无效")
                # 停止定时验证
                self.cookie_timer.stop()
                QMessageBox.warning(self, "失败", message)
        except Exception as e:
            self.current_cookie = None
            self.cookie_import_icon.setStyleSheet("color: red;")
            self.cookie_import_text.setText("验证失败")
            self.cookie_verify_icon.setStyleSheet("color: red;")
            self.cookie_verify_text.setText("无效")
            # 停止定时验证
            self.cookie_timer.stop()
            QMessageBox.critical(self, "错误", f"验证Cookies时出错: {str(e)}")
            
    def auto_verify_cookies(self):
        """自动验证Cookie有效性，仅在失效时显示提示"""
        try:
            if not self.current_cookie:
                return
                
            logger.info("开始自动验证Cookie有效性...")
            valid, _ = self.cookie_manager.verify_cookies(self.current_cookie)
            
            if valid:
                self.cookie_verify_icon.setStyleSheet("color: green;")
                self.cookie_verify_text.setText("有效")
                logger.info("自动验证Cookie: 有效")
            else:
                self.current_cookie = None
                self.cookie_verify_icon.setStyleSheet("color: red;")
                self.cookie_verify_text.setText("无效")
                logger.warning("自动验证Cookie: 无效")
                # 仅在Cookie失效时显示通知
                QMessageBox.warning(self, "Cookie已失效", "Cookie已失效，请重新导入并验证Cookie")
                # 停止定时验证
                self.cookie_timer.stop()
        except Exception as e:
            self.current_cookie = None
            self.cookie_verify_icon.setStyleSheet("color: red;")
            self.cookie_verify_text.setText("无效")
            logger.error(f"自动验证Cookie时出错: {str(e)}")
            # 停止定时验证
            self.cookie_timer.stop()
            
    def copy_cookies(self):
        """复制Cookies"""
        try:
            success, cookies_json = self.cookie_manager.load_cookies_json()
            if not success:
                QMessageBox.warning(self, "警告", cookies_json)
                return
                
            clipboard = QApplication.clipboard()
            clipboard.setText(cookies_json)
            QMessageBox.information(self, "成功", "Cookies已复制到剪贴板")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"复制Cookies时出错: {str(e)}")

    def save_data(self):
        """保存数据到Excel文件"""
        try:
            if not hasattr(self, 'current_data') or self.current_data is None:
                QMessageBox.warning(self, "警告", "没有可保存的数据")
                return
                
            # 获取保存文件路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存数据",
                "抖音评论数据.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )
            
            if file_path:
                # 如果用户没有指定.xlsx后缀，添加它
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                    
                # 保存数据到Excel
                self.current_data.to_excel(file_path, index=False, engine='openpyxl')
                self.add_log(f"数据已保存到: {file_path}")
                QMessageBox.information(self, "成功", "数据已成功保存到Excel文件")
                
        except Exception as e:
            error_msg = f"保存数据时出错:\n{str(e)}"
            logger.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)

    def create_ai_analysis_tab(self):
        """创建AI分析标签页"""
        ai_tab = QWidget()
        layout = QVBoxLayout()
        
        # API Key设置组
        api_group = QGroupBox("DeepSeek API设置")
        api_layout = QHBoxLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入DeepSeek API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # 密码模式显示
        
        verify_btn = QPushButton("验证API Key")
        verify_btn.clicked.connect(self.verify_api_key)
        
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(verify_btn)
        api_group.setLayout(api_layout)
        
        # AI分析区域
        analysis_group = QGroupBox("AI分析")
        analysis_layout = QVBoxLayout()
        
        # 分析按钮区域
        buttons_layout = QHBoxLayout()
        
        # 默认分析按钮
        analyze_btn = QPushButton("开始AI分析")
        analyze_btn.setObjectName("开始AI分析")  # 设置对象名，用于后续查找
        analyze_btn.clicked.connect(self.start_ai_analysis)
        buttons_layout.addWidget(analyze_btn)
        
        analysis_layout.addLayout(buttons_layout)
        
        # 自定义提问区域
        custom_group = QGroupBox("自定义提问")
        custom_layout = QVBoxLayout()
        
        # 提示标签
        hint_label = QLabel("在下方输入您的问题，AI将基于已采集的评论数据进行回答：")
        custom_layout.addWidget(hint_label)
        
        # 问题输入框
        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("例如：这些评论中最关注的问题是什么？用户对产品最不满意的地方是什么？")
        self.question_input.setMaximumHeight(100)
        custom_layout.addWidget(self.question_input)
        
        # 提问按钮
        ask_btn = QPushButton("向AI提问")
        ask_btn.clicked.connect(self.ask_ai_question)
        custom_layout.addWidget(ask_btn)
        
        # 添加自定义提问区域
        analysis_layout.addWidget(custom_group)
        custom_group.setLayout(custom_layout)
        
        # 分析结果显示区域
        result_label = QLabel("分析结果：")
        analysis_layout.addWidget(result_label)
        
        self.analysis_result = QTextEdit()
        self.analysis_result.setReadOnly(True)
        self.analysis_result.setPlaceholderText("AI分析结果将在这里显示")
        analysis_layout.addWidget(self.analysis_result)
        
        analysis_group.setLayout(analysis_layout)
        
        # 添加到主布局
        layout.addWidget(api_group)
        layout.addWidget(analysis_group)
        ai_tab.setLayout(layout)
        
        # 加载保存的API Key
        if self.deepseek_api.api_key:
            self.api_key_input.setText(self.deepseek_api.api_key)
        
        # 添加到标签页
        self.tab_widget.addTab(ai_tab, "AI分析")
        
    def verify_api_key(self):
        """验证API Key"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API Key")
            return
            
        if self.deepseek_api.verify_api_key(api_key):
            self.deepseek_api.save_api_key(api_key)
            QMessageBox.information(self, "成功", "API Key验证成功并已保存")
        else:
            QMessageBox.warning(self, "错误", "API Key验证失败，请检查是否正确")

    def start_ai_analysis(self):
        """开始AI分析"""
        if not self.deepseek_api.api_key:
            QMessageBox.warning(self, "警告", "请先设置并验证API Key")
            return
            
        if not hasattr(self, 'current_data') or self.current_data is None or self.current_data.empty:
            QMessageBox.warning(self, "警告", "请先采集评论数据")
            return
            
        # 准备评论文本
        comments_text = self.current_data['评论内容'].str.cat(sep='\n')
        
        # 创建并启动分析线程
        self.analysis_worker = AIAnalysisWorker(
            self.deepseek_api, 
            comments_text,
            custom_prompt=None  # 使用默认分析模式
        )
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.start()
        
        # 禁用所有按钮
        self.disable_analysis_buttons()
        self.analysis_result.setText("正在进行AI分析，请稍候...")

    def on_analysis_finished(self, result):
        """AI分析完成回调"""
        self.analysis_result.setText(result)
        self.enable_analysis_buttons()

    def on_analysis_error(self, error_msg):
        """AI分析错误回调"""
        QMessageBox.warning(self, "错误", f"AI分析失败: {error_msg}")
        self.enable_analysis_buttons()

    def create_collection_tab(self):
        """创建评论采集标签页"""
        comment_tab = QWidget()
        comment_layout = QVBoxLayout()
        
        # 创建输入区域
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请粘贴抖音分享链接")
        self.get_replies_checkbox = QCheckBox("获取评论回复")
        self.start_button = QPushButton("开始采集")
        self.save_button = QPushButton("保存数据")
        self.start_button.clicked.connect(self.start_collection)
        self.save_button.clicked.connect(self.save_data)
        self.save_button.setEnabled(False)
        
        input_layout.addWidget(QLabel("分享链接:"))
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.get_replies_checkbox)
        input_layout.addWidget(self.start_button)
        input_layout.addWidget(self.save_button)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 创建日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(100)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "评论ID", "评论内容", "点赞数", "评论时间",
            "用户昵称", "用户抖音号", "IP归属", "回复总数"
        ])
        # 设置表格列宽自动调整
        header = self.table.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # 添加到主布局
        comment_layout.addLayout(input_layout)
        comment_layout.addWidget(self.progress_bar)
        comment_layout.addWidget(QLabel("运行日志:"))
        comment_layout.addWidget(self.log_display)
        comment_layout.addWidget(self.table)
        
        comment_tab.setLayout(comment_layout)
        
        # 添加到标签页
        self.tab_widget.addTab(comment_tab, "评论采集")

    def create_cookie_tab(self):
        """创建Cookie管理标签页"""
        cookie_tab = QWidget()
        cookie_layout = QVBoxLayout()
        
        # Cookie输入区域
        cookie_input_label = QLabel("请粘贴JSON格式的Cookies:")
        self.cookie_input = QTextEdit()
        self.cookie_input.setPlaceholderText("在此粘贴从Cookie Editor导出的JSON内容...")
        cookie_layout.addWidget(cookie_input_label)
        cookie_layout.addWidget(self.cookie_input)
        
        # Cookie操作按钮
        cookie_buttons_layout = QHBoxLayout()
        self.import_cookie_btn = QPushButton("导入Cookies")
        self.verify_cookie_btn = QPushButton("验证Cookies")
        self.copy_cookie_btn = QPushButton("复制Cookies")
        
        self.import_cookie_btn.clicked.connect(self.import_cookies)
        self.verify_cookie_btn.clicked.connect(self.verify_cookies)
        self.copy_cookie_btn.clicked.connect(self.copy_cookies)
        
        cookie_buttons_layout.addWidget(self.import_cookie_btn)
        cookie_buttons_layout.addWidget(self.verify_cookie_btn)
        cookie_buttons_layout.addWidget(self.copy_cookie_btn)
        
        cookie_layout.addLayout(cookie_buttons_layout)
        
        cookie_tab.setLayout(cookie_layout)
        
        # 添加到标签页
        self.tab_widget.addTab(cookie_tab, "Cookie管理")
        
        # 尝试加载保存的Cookies
        self.load_saved_cookies()

    def ask_ai_question(self):
        """处理自定义AI提问"""
        if not self.deepseek_api.api_key:
            QMessageBox.warning(self, "警告", "请先设置并验证API Key")
            return
            
        if not hasattr(self, 'current_data') or self.current_data is None or self.current_data.empty:
            QMessageBox.warning(self, "警告", "请先采集评论数据")
            return
            
        question = self.question_input.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, "警告", "请输入您的问题")
            return
            
        # 准备评论文本
        comments_text = self.current_data['评论内容'].str.cat(sep='\n')
        
        # 创建并启动分析线程
        self.analysis_worker = AIAnalysisWorker(
            self.deepseek_api, 
            comments_text,
            custom_prompt=f"""请基于以下抖音评论内容，回答用户的问题：

问题：{question}

评论内容：
{comments_text}
"""
        )
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.start()
        
        # 禁用所有按钮
        self.disable_analysis_buttons()
        self.analysis_result.setText("正在思考您的问题，请稍候...")

    def disable_analysis_buttons(self):
        """禁用所有分析相关按钮"""
        # 禁用默认分析按钮
        analyze_btn = self.tab_widget.findChild(QPushButton, "开始AI分析")
        if analyze_btn:
            analyze_btn.setEnabled(False)
        
        # 禁用提问按钮和输入框
        for widget in self.tab_widget.findChildren(QPushButton):
            if widget.text() == "向AI提问":
                widget.setEnabled(False)
        self.question_input.setEnabled(False)

    def enable_analysis_buttons(self):
        """启用所有分析相关按钮"""
        # 启用默认分析按钮
        analyze_btn = self.tab_widget.findChild(QPushButton, "开始AI分析")
        if analyze_btn:
            analyze_btn.setEnabled(True)
        
        # 启用提问按钮和输入框
        for widget in self.tab_widget.findChildren(QPushButton):
            if widget.text() == "向AI提问":
                widget.setEnabled(True)
        self.question_input.setEnabled(True)

def main():
    try:
        # 创建应用
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = f"程序启动失败:\n{str(e)}\n\n堆栈跟踪:\n{traceback.format_exc()}"
        logger.error(error_msg)
        QMessageBox.critical(None, "严重错误", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main() 