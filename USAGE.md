# 使用说明

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果遇到网络问题,可以使用国内镜像:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 启动服务

**方法一: 使用启动脚本 (推荐)**

```bash
chmod +x start.sh
./start.sh
```

**方法二: 手动启动**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**方法三: 指定端口启动**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

### 3. 访问应用

- **Web界面**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 功能使用

### 📥 下载单个视频

#### Web界面方式:

1. 打开Web界面
2. 进入"视频下载"标签页
3. 粘贴小红书视频链接
4. 选择画质(高清/标清/流畅)
5. 点击"创建下载任务"

#### API方式:

```bash
# 创建任务
curl -X POST "http://localhost:8000/api/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.xiaohongshu.com/explore/xxxxxxxxx",
    "quality": "hd"
  }'

# 获取任务ID后启动
curl -X POST "http://localhost:8000/api/tasks/{task_id}/start"
```

### 📋 管理下载任务

#### 查看所有任务

```bash
curl "http://localhost:8000/api/tasks/"
```

#### 查看特定任务

```bash
curl "http://localhost:8000/api/tasks/{task_id}"
```

#### 暂停任务

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/pause"
```

#### 恢复任务

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/resume"
```

#### 停止任务

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/stop"
```

#### 重试失败任务

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/retry"
```

#### 删除任务

```bash
curl -X DELETE "http://localhost:8000/api/tasks/{task_id}"
```

### 🔐 配置Cookie

某些功能需要登录后的Cookie才能使用:

#### 获取Cookie步骤:

1. 打开Chrome浏览器
2. 访问 https://www.xiaohongshu.com
3. 登录你的账号
4. 按 `F12` 打开开发者工具
5. 切换到 `Network` (网络)标签
6. 刷新页面
7. 点击任意一个请求
8. 在请求头中找到 `Cookie` 字段
9. 复制完整的Cookie字符串

#### Web界面配置:

1. 进入"认证设置"标签页
2. 粘贴Cookie字符串
3. 点击"保存Cookie"

#### API方式配置:

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "cookies": "your-cookie-string-here"
  }'
```

#### 验证Cookie:

```bash
curl -X POST "http://localhost:8000/api/auth/validate" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "your-cookie-string"}'
```

### 📚 收藏夹功能

#### 添加收藏夹

```bash
curl -X POST "http://localhost:8000/api/favorites/" \
  -H "Content-Type: application/json" \
  -d '{
    "favorite_id": "your-favorite-id",
    "name": "我的收藏夹"
  }'
```

#### 同步收藏夹

同步收藏夹会从小红书获取最新的视频列表:

```bash
curl -X POST "http://localhost:8000/api/favorites/{favorite_id}/sync"
```

#### 批量下载收藏夹

```bash
curl -X POST "http://localhost:8000/api/favorites/{favorite_id}/download-all"
```

#### 检测失效视频

```bash
curl -X POST "http://localhost:8000/api/favorites/{favorite_id}/check-invalid"
```

### 📹 获取视频信息

在下载前,可以先获取视频信息:

```bash
curl "http://localhost:8000/api/videos/info?url=https://www.xiaohongshu.com/explore/xxxx"
```

返回信息包括:
- 视频标题
- 作者信息
- 封面图
- 可用画质
- 分P信息

## 配置选项

### 环境变量

创建 `.env` 文件自定义配置:

```env
# 应用配置
APP_NAME=小红书视频下载工具
APP_VERSION=1.0.0
DEBUG=true

# 数据库
DATABASE_URL=sqlite:///./xiaohongshu_downloader.db

# 下载设置
DOWNLOAD_DIR=./downloads          # 下载目录
MAX_CONCURRENT_DOWNLOADS=3        # 最大并发数
CHUNK_SIZE=1048576               # 下载块大小 (1MB)
RETRY_TIMES=3                    # 重试次数
TIMEOUT=30                       # 超时时间(秒)

# Cookie存储
COOKIE_FILE=./cookies.json
```

### 修改下载目录

方法一: 修改 `.env` 文件

```env
DOWNLOAD_DIR=/path/to/your/downloads
```

方法二: 直接修改 `app/config.py`

```python
DOWNLOAD_DIR: str = "/path/to/your/downloads"
```

## 常见问题

### Q1: 如何下载多个视频?

A: 可以创建多个下载任务,系统会自动管理并发下载。

### Q2: 下载失败怎么办?

A:
1. 检查网络连接
2. 检查视频链接是否有效
3. 尝试配置Cookie
4. 使用"重试"功能

### Q3: 如何实现断点续传?

A: 系统自动支持断点续传。暂停任务后,临时文件会保留,恢复任务时会从上次位置继续下载。

### Q4: 可以下载私密视频吗?

A: 需要配置登录后的Cookie,确保账号有权限访问该视频。

### Q5: 下载速度慢怎么办?

A:
1. 检查网络带宽
2. 调整并发下载数量
3. 选择较低的画质

## 性能优化

### 提高下载速度

1. **增加并发数**:
   ```env
   MAX_CONCURRENT_DOWNLOADS=5
   ```

2. **增大下载块**:
   ```env
   CHUNK_SIZE=2097152  # 2MB
   ```

3. **使用有线网络**

### 减少资源占用

1. **减少并发数**:
   ```env
   MAX_CONCURRENT_DOWNLOADS=1
   ```

2. **及时清理已完成任务**

3. **定期清理下载目录**

## 安全建议

1. **保护Cookie**:
   - Cookie包含登录凭证,不要泄露给他人
   - 定期更换Cookie

2. **合法使用**:
   - 仅下载有权限访问的内容
   - 遵守版权法律
   - 尊重作者权益

3. **网络安全**:
   - 不要在公共网络使用
   - 建议使用HTTPS

## 故障排查

### 应用无法启动

```bash
# 检查Python版本
python3 --version  # 需要 3.7+

# 检查依赖
pip list | grep fastapi

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 数据库错误

```bash
# 删除数据库文件重新初始化
rm xiaohongshu_downloader.db

# 重启应用
./start.sh
```

### 下载失败

1. 检查日志输出
2. 验证Cookie有效性
3. 确认视频链接正确
4. 检查磁盘空间

## 开发模式

### 启用调试模式

```bash
# 设置环境变量
export DEBUG=true

# 启动应用
uvicorn app.main:app --reload --log-level debug
```

### 查看日志

应用会输出详细的调试信息到控制台。

### 运行测试

```bash
pytest
```

## 更新日志

### v1.0.0
- ✅ 初始版本发布
- ✅ 支持单视频下载
- ✅ 任务管理功能
- ✅ 收藏夹管理
- ✅ Web管理界面
- ✅ Cookie认证
- ✅ 断点续传
- ✅ 多画质支持

## 技术栈

- **后端**: FastAPI
- **数据库**: SQLite + SQLAlchemy
- **HTTP客户端**: httpx
- **前端**: 原生 HTML/CSS/JavaScript
- **UI设计**: 现代化渐变设计

## 贡献指南

欢迎贡献代码!请遵循以下步骤:

1. Fork本项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 获取帮助

如有问题:
1. 查看本文档
2. 查看API文档: http://localhost:8000/docs
3. 提交Issue

---

**享受下载吧! 🎉**
