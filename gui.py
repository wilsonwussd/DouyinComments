import sys
import os
import asyncio
import pandas as pd
import traceback
import re
import requests
from urllib.parse import urlparse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QCheckBox, QProgressBar, QMessageBox, QHeaderView,
    QTextEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from main import fetch_all_comments_async, fetch_all_replies_async, process_comments, process_replies, load_cookie
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

    def __init__(self, aweme_id, get_replies=False):
        super().__init__()
        self.aweme_id = aweme_id
        self.get_replies = get_replies

    def run(self):
        try:
            self.log.emit("开始创建事件循环...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.log.emit(f"开始获取视频 {self.aweme_id} 的评论...")
            comments = loop.run_until_complete(fetch_all_comments_async(self.aweme_id))
            if not comments:
                raise Exception("未获取到评论数据，请检查视频ID是否正确")
                
            self.log.emit("处理评论数据...")
            comments_df = process_comments(comments)
            self.log.emit(f"成功获取 {len(comments)} 条评论")
            
            if self.get_replies:
                self.log.emit("开始获取评论回复...")
                replies = loop.run_until_complete(fetch_all_replies_async(comments))
                self.log.emit(f"成功获取 {len(replies)} 条回复")
                replies_df = process_replies(replies, comments_df)
                result = pd.concat([comments_df, replies_df], ignore_index=True)
                self.log.emit(f"总计获取 {len(result)} 条数据")
            else:
                result = comments_df
                
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = f"错误详情:\n{str(e)}\n\n堆栈跟踪:\n{traceback.format_exc()}"
            logger.error(error_msg)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音评论采集工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建输入选择区域
        input_type_layout = QHBoxLayout()
        self.input_type_group = QButtonGroup()
        self.video_id_radio = QRadioButton("视频ID")
        self.share_link_radio = QRadioButton("分享链接")
        self.video_id_radio.setChecked(True)
        self.input_type_group.addButton(self.video_id_radio)
        self.input_type_group.addButton(self.share_link_radio)
        input_type_layout.addWidget(self.video_id_radio)
        input_type_layout.addWidget(self.share_link_radio)
        input_type_layout.addStretch()
        
        # 创建输入区域
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入视频ID或分享链接")
        self.get_replies_checkbox = QCheckBox("获取评论回复")
        self.start_button = QPushButton("开始采集")
        self.start_button.clicked.connect(self.start_collection)
        
        input_layout.addWidget(QLabel("输入:"))
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.get_replies_checkbox)
        input_layout.addWidget(self.start_button)
        
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
        layout.addLayout(input_type_layout)
        layout.addLayout(input_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(QLabel("运行日志:"))
        layout.addWidget(self.log_display)
        layout.addWidget(self.table)
        
        main_widget.setLayout(layout)
        
        # 初始化工作线程
        self.worker = None
        
        # 添加日志
        self.add_log("程序已启动，等待输入...")
        
        # 连接单选按钮信号
        self.video_id_radio.toggled.connect(self.update_input_placeholder)
        self.share_link_radio.toggled.connect(self.update_input_placeholder)

    def update_input_placeholder(self):
        """更新输入框的提示文本"""
        if self.video_id_radio.isChecked():
            self.input_field.setPlaceholderText("请输入视频ID")
        else:
            self.input_field.setPlaceholderText("请输入分享链接")

    def add_log(self, message):
        """添加日志到显示区域"""
        self.log_display.append(f"{message}")
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def start_collection(self):
        """开始采集评论"""
        try:
            input_text = self.input_field.text().strip()
            if not input_text:
                QMessageBox.warning(self, "警告", "请输入视频ID或分享链接")
                return
            
            video_id = input_text
            if self.share_link_radio.isChecked():
                # 解析分享链接
                self.add_log("正在解析分享链接...")
                video_id = extract_video_id(input_text)
                if not video_id:
                    QMessageBox.warning(self, "警告", "无法从分享链接中提取视频ID")
                    return
                self.add_log(f"成功提取视频ID: {video_id}")
            
            # 验证视频ID格式
            if not video_id.isdigit():
                QMessageBox.warning(self, "警告", "视频ID必须是数字")
                return
                
            # 清空日志显示
            self.log_display.clear()
            self.add_log(f"开始采集视频ID: {video_id} 的评论...")
            
            # 禁用开始按钮
            self.start_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 显示忙碌状态
            
            # 创建并启动工作线程
            self.worker = CommentWorker(video_id, self.get_replies_checkbox.isChecked())
            self.worker.finished.connect(self.on_collection_finished)
            self.worker.error.connect(self.on_error)
            self.worker.log.connect(self.add_log)
            self.worker.start()
            
        except Exception as e:
            error_msg = f"启动采集时出错:\n{str(e)}\n\n堆栈跟踪:\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.on_error(error_msg)

    def on_collection_finished(self, data):
        """采集完成的回调函数"""
        try:
            # 清空表格
            self.table.setRowCount(0)
            
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
            
            # 添加日志
            self.add_log(f"数据采集完成，共获取 {self.table.rowCount()} 条数据")
            
            # 显示完成消息
            QMessageBox.information(self, "提示", f"采集完成，共获取 {self.table.rowCount()} 条数据")
            
        except Exception as e:
            error_msg = f"处理数据时出错:\n{str(e)}\n\n堆栈跟踪:\n{traceback.format_exc()}"
            logger.error(error_msg)
            self.on_error(error_msg)

    def on_error(self, error_msg):
        """错误处理"""
        self.start_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.add_log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"采集过程中出现错误：\n{error_msg}")

def main():
    try:
        # 加载cookie
        logger.info("正在加载cookie...")
        load_cookie()
        
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