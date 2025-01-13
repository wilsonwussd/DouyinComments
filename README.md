# 抖音评论采集工具 V2.0

一个功能强大的抖音视频评论采集工具，支持图形界面操作，具有评论采集和Cookie管理功能。

## 功能特点

### 评论采集
- ✨ 支持采集一级评论和二级评论（回复）
- 🚀 异步请求技术，采集速度快
- 🔄 自动处理请求频率限制
- 💾 数据保存为CSV格式
- 🔍 支持直接输入视频ID或分享链接
- 📊 实时显示采集进度和状态
- 📝 详细的运行日志记录

### Cookie管理
- 📥 支持导入JSON格式的Cookies
- ✅ 自动验证Cookies有效性
- 💫 一键保存和格式化Cookies
- 📋 快速复制Cookies功能
- 🔔 实时显示Cookie状态

## 环境要求
- Python 3.8+
- 相关依赖包（见 requirements.txt）

## 安装步骤

1. 克隆项目到本地
```bash
git clone https://github.com/your-username/DouyinComments.git
cd DouyinComments
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动程序
```bash
python gui.py
```

### Cookie管理
1. 点击"Cookie管理"标签页
2. 从浏览器导出JSON格式的Cookies（推荐使用Cookie Editor插件）
3. 将Cookies内容粘贴到输入框
4. 点击"导入Cookies"按钮保存
5. 使用"验证Cookies"按钮检查有效性

### 评论采集
1. 点击"评论采集"标签页
2. 选择输入类型（视频ID/分享链接）
3. 输入视频ID或分享链接
4. 选择是否获取评论回复
5. 点击"开始采集"按钮
6. 等待采集完成，数据将显示在表格中

## 数据字段说明
- 评论ID：评论的唯一标识
- 评论内容：评论的具体内容
- 点赞数：评论获得的点赞数量
- 评论时间：评论发布的时间
- 用户昵称：评论用户的昵称
- 用户抖音号：评论用户的抖音号
- IP归属：评论用户的IP归属地
- 回复总数：评论的回复数量

## 注意事项
1. 首次使用需要导入有效的Cookies
2. Cookies具有时效性，失效后需要重新导入
3. 建议使用Cookie Editor插件导出Cookies
4. 采集频率过高可能导致IP被限制

## 更新日志

### V2.0
- 新增图形用户界面
- 添加Cookie管理功能
- 支持分享链接解析
- 优化错误处理和日志记录
- 改进代码结构和注释

### V1.0
- 基础评论采集功能
- 命令行界面
- CSV数据导出

## 问题反馈
如果您在使用过程中遇到任何问题，请通过以下方式反馈：
1. 在GitHub上提交Issue
2. 发送邮件至开发者邮箱

## 免责声明
本工具仅供学习交流使用，请勿用于任何商业用途。使用本工具所产生的一切后果由使用者自行承担。
