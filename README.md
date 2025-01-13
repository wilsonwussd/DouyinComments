# 抖音评论采集工具

一个简单易用的抖音视频评论采集工具，支持GUI界面操作，自动管理Cookie，采集评论数据并支持导出Excel格式。

## 🌟 功能特点

- ✨ 图形化界面，简单易用
- 🔄 支持从分享链接自动提取视频ID
- 🍪 Cookie管理系统
  - 支持导入JSON格式的Cookie
  - 自动验证Cookie有效性
  - 定时检查Cookie状态（每5分钟）
  - 实时显示Cookie状态
- 📝 评论数据采集
  - 支持采集一级评论
  - 可选择是否采集评论回复
  - 采集过程实时显示进度
  - 无评论数量限制
- 💾 数据本地保存
  - 支持导出Excel格式（.xlsx）
  - 保存为CSV格式
  - 包含评论ID、内容、点赞数等信息

## 🆕 最新更新

1. 界面优化
   - 修复macOS字体兼容性问题
   - 优化字体显示效果
   - 改进界面布局和交互

2. 评论采集增强
   - 修复webid缺失问题
   - 提升评论获取稳定性
   - 优化错误处理机制
   - 改进数据处理流程

3. 数据导出功能
   - 支持Excel格式导出
   - 自定义保存路径
   - 导出完整评论数据

4. 系统稳定性
   - 完善错误提示信息
   - 优化异常处理流程
   - 提升运行稳定性

## 💻 界面说明

### Cookie管理页面
![Cookie管理页面](docs/images/cookie_management.png)

1. Cookie导入区域
   - 文本框：粘贴从浏览器导出的JSON格式Cookie
   - 导入按钮：保存Cookie到本地
   - 验证按钮：检查Cookie有效性
   - 复制按钮：复制当前Cookie到剪贴板

### 评论采集页面
![评论采集页面](docs/images/comment_collection.png)

1. 输入区域
   - 分享链接输入框：粘贴抖音视频分享链接
   - 评论回复选项：是否采集评论的回复
   - 开始采集按钮：启动采集过程
   - 保存数据按钮：将数据导出为Excel文件

2. 数据显示
   - 运行日志：显示采集过程的实时状态
   - 数据表格：展示采集到的评论数据

## 📝 使用方法

1. Cookie准备
   - 在浏览器中登录抖音网页版
   - 使用Cookie Editor等工具导出Cookie为JSON格式
   - 复制JSON格式的Cookie内容

2. Cookie导入
   - 打开软件，进入"Cookie管理"标签页
   - 将JSON格式Cookie粘贴到输入框
   - 点击"导入Cookies"按钮
   - 点击"验证Cookies"按钮确认有效性

3. 评论采集
   - 切换到"评论采集"标签页
   - 从抖音复制视频分享链接
   - 粘贴到输入框
   - 选择是否需要获取评论回复
   - 点击"开始采集"

4. 数据导出
   - 采集完成后点击"保存数据"按钮
   - 选择保存位置和文件名
   - 数据将以Excel格式保存

## ⚠️ 注意事项

1. Cookie有效期
   - Cookie可能会定期失效，需要重新导入
   - 软件会自动检测Cookie状态（每5分钟）
   - Cookie失效时会提示更新

2. 数据采集
   - 采集前会自动验证Cookie有效性
   - 如遇到采集失败，请检查Cookie状态
   - 建议定期更新Cookie以确保稳定性

## 🔧 环境要求

- Python 3.8+
- PyQt6
- pandas
- httpx
- requests
- loguru
- openpyxl

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 运行程序

```bash
python gui.py
```

## 📄 开源协议

本项目遵循 MIT 协议开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目！
