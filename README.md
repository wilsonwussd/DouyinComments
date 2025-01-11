# 抖音评论采集工具 V1.0

这是一个用于采集抖音视频评论的工具，支持获取一级评论和二级评论（回复）。

## 功能特点

- ✅ 支持采集一级评论
- ✅ 支持采集二级评论（回复）
- ✅ 支持获取评论中的图片
- ✅ 自动处理请求频率限制
- ✅ 数据保存为CSV格式
- ✅ 支持断点续传

## 环境要求

- Python 3.8+
- Node.js（用于执行JS代码）
- 相关Python包（见 requirements.txt）

## 安装步骤

1. 克隆代码库：
```bash
git clone https://github.com/wilsonwussd/DouyinComments.git
cd DouyinComments
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置cookie：
   - 创建 cookie.txt 文件
   - 从抖音网页版获取cookie并写入文件

## 使用方法

### 方法一：一次性获取所有评论（适合评论数量较少的视频）

```bash
python main.py
```

### 方法二：分步获取评论（适合评论数量较多的视频）

1. 先获取一级评论：
```bash
python fetch_comments.py
```

2. 再获取二级评论：
```bash
python fetch_replies.py
```

## 输出文件

程序会在以下位置生成CSV文件：

- 方法一：`data/v1/<aweme_id>/`
- 方法二：`data/<aweme_id>/`

包含以下文件：
- `comments.csv`：一级评论数据
- `replies.csv`：二级评论数据

## 注意事项

1. 使用前需要先获取抖音网页版的cookie
2. 建议使用登录状态的cookie以获取完整数据
3. 如遇到请求频率限制，程序会自动等待一段时间后重试
4. 支持断点续传，意外中断后可以继续采集

## 免责声明

本工具仅供学习交流使用，请勿用于非法用途。使用本工具时请遵守相关法律法规，如造成任何问题，与本工具作者无关。

## 参考项目

感谢以下项目的启发：
- [ShilongLee/Crawler](https://github.com/ShilongLee/Crawler)
