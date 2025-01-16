# 抖音评论采集工具 v1.2.1

一个用于采集抖音视频评论的桌面工具，支持AI分析功能。

## 最新更新

### v1.2.1 更新内容
1. 账号安全优化
   - 新增账号互斥登录功能，防止账号被多处同时登录
   - 完善异常登录提示，包括账号异地登录、登录过期等情况

2. 界面交互优化
   - 优化登录窗口提示信息
   - 新增友好的状态提示窗口
   - 改进错误提示的显示方式

3. 安全性提升
   - 新增token有效性验证
   - 自动检测异常登录行为
   - 完善登录状态管理

4. 其他改进
   - 优化程序启动流程
   - 改进错误处理机制
   - 提升整体运行稳定性

## 功能特点

1. 评论采集
   - 支持采集视频评论和回复
   - 自动处理评论分页
   - 支持导出Excel格式

2. AI分析
   - 集成DeepSeek AI分析
   - 支持自定义分析问题
   - 智能评论内容分析

3. Cookie管理
   - 可视化Cookie导入
   - 自动Cookie验证
   - 定时检查Cookie有效性

4. 账号安全
   - 账号互斥登录保护
   - 自动检测登录状态
   - 异常登录提醒

## 使用说明

### 1. 安装和运行
1. 确保已安装Python 3.8或更高版本
2. 安装依赖：`pip install -r requirements.txt`
3. 运行程序：`python gui.py`

### 2. 登录说明
- 首次使用需要登录账号
- 同一账号不可在多处同时登录
- 如在其他设备登录，当前设备会自动退出

### 3. Cookie设置
1. 打开Chrome浏览器，登录抖音网页版
2. 使用Cookie导出工具导出Cookie
3. 在软件中导入Cookie文件
4. 等待Cookie验证完成

### 4. 评论采集
1. 输入抖音视频链接
2. 选择采集模式（评论/回复）
3. 点击开始采集
4. 等待采集完成后导出数据

### 5. AI分析
1. 确保已设置DeepSeek API Key
2. 选择需要分析的评论数据
3. 使用默认分析或自定义问题
4. 等待AI分析结果

## 注意事项

1. 账号安全
   - 请勿将账号密码分享给他人
   - 发现异地登录时及时修改密码
   - 定期检查登录设备情况

2. Cookie使用
   - Cookie有效期通常为7天
   - 建议及时更新过期的Cookie
   - 不要将Cookie分享给他人

3. 采集限制
   - 遵守抖音平台的使用规范
   - 避免频繁、大量的采集请求
   - 建议设置适当的采集间隔

4. 其他说明
   - 定期更新软件版本
   - 及时备份重要数据
   - 遇到问题及时反馈

## 常见问题

1. 登录相关
   - Q: 为什么提示"账号已在其他设备登录"？
   - A: 系统检测到您的账号在其他地方登录，为保护账号安全，当前设备会自动退出。

2. Cookie相关
   - Q: Cookie验证失败怎么办？
   - A: 请重新获取并导入Cookie，确保使用的是最新的Cookie数据。

3. 采集相关
   - Q: 采集过程中断该怎么办？
   - A: 检查网络连接和Cookie状态，确保都正常后重新开始采集。

## 技术支持

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件至：[support@example.com]

## 免责声明

本工具仅供学习研究使用，请勿用于非法用途。使用本工具所产生的一切后果由使用者自行承担。
