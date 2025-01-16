@echo off
chcp 65001
setlocal EnableDelayedExpansion

REM 设置工作目录为批处理文件所在目录
cd /d "%~dp0"

REM 清理旧的构建文件
echo [INFO] 清理旧文件...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "release" rd /s /q "release"
if exist "*.spec" del /f /q "*.spec"

REM 检查 Python 安装
echo [INFO] 检查 Python 环境...
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python未安装或未添加到PATH
    pause
    exit /b 1
)

REM 安装依赖
echo [INFO] 安装依赖...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install "pyinstaller==6.3.0"
python -m pip install "pillow"
python -m pip install "PyQt6"
python -m pip install "pandas"
python -m pip install "httpx"
python -m pip install "requests"
python -m pip install "loguru"
python -m pip install "openpyxl"

REM 生成spec文件
echo [INFO] 生成spec文件...
python -m PyInstaller --name "抖音评论采集工具" --add-data "README.md;." --add-data "requirements.txt;." --add-data "cookie.txt;." --add-data "cookie_json.txt;." --add-data "deepseek_api_key.txt;." --hidden-import PyQt6 --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.sip --hidden-import pandas --hidden-import pandas._libs.tslibs.base --hidden-import pandas._libs.tslibs.np_datetime --hidden-import pandas._libs.tslibs.timedeltas --hidden-import pandas._libs.tslibs.timestamps --hidden-import httpx --hidden-import requests --hidden-import loguru --hidden-import openpyxl --hidden-import asyncio --hidden-import json --hidden-import urllib --hidden-import re --hidden-import traceback --hidden-import os --hidden-import sys --hidden-import numpy --hidden-import charset_normalizer.md__mypyc --console gui.py

REM 检查spec文件是否生成
if not exist "抖音评论采集工具.spec" (
    echo [ERROR] spec文件生成失败
    pause
    exit /b 1
)

REM 打包应用
echo [INFO] 打包应用...
python -m PyInstaller --clean "抖音评论采集工具.spec"

REM 检查是否成功生成exe
if not exist "dist\抖音评论采集工具.exe" (
    echo [ERROR] 打包失败，未生成exe文件
    pause
    exit /b 1
)

REM 创建发布目录
echo [INFO] 创建发布包...
md "release" 2>nul

REM 复制文件到发布目录
echo [INFO] 复制文件...
copy "dist\抖音评论采集工具.exe" "release\"
if exist "使用说明.txt" copy "使用说明.txt" "release\"
if exist "README.md" copy "README.md" "release\"
if exist "cookie.txt" copy "cookie.txt" "release\"
if exist "cookie_json.txt" copy "cookie_json.txt" "release\"
if exist "deepseek_api_key.txt" copy "deepseek_api_key.txt" "release\"

echo [INFO] 构建完成！
echo [INFO] 生成的文件在 release 目录中
dir "release"
pause 