# 小红书视频下载工具

功能完整的小红书视频下载工具,支持单视频下载、批量下载、收藏夹管理等功能。

## ✨ 功能特性

### 📥 视频下载
- ✅ 单P/多P视频下载
- ✅ 选择分P下载
- ✅ 断点续传
- ✅ 多画质支持 (高清/标清/流畅)
- ✅ 重新下载

### 📋 任务管理
- ✅ 创建、查看、删除任务
- ✅ 停止/暂停/恢复下载
- ✅ 实时进度追踪
- ✅ 下载速度显示
- ✅ 任务状态管理

### 📚 收藏夹
- ✅ 列表获取与详情
- ✅ 批量下载
- ✅ 失效检测与筛选
- ✅ 自动同步

### 🔐 用户认证
- ✅ Cookie登录
- ✅ Cookie验证
- ✅ 自动保存认证状态

### 🌐 Web界面
- ✅ 完整的Web管理界面
- ✅ 实时任务监控
- ✅ 直观的进度显示
- ✅ 响应式设计

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 使用启动脚本
./start.sh

# 或手动启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问Web界面

打开浏览器访问: http://localhost:8000

### 4. 访问API文档

打开浏览器访问: http://localhost:8000/docs

## 📖 使用说明

### 方式一: Web界面操作

1. **设置Cookie (可选)**
   - 访问"认证设置"标签页
   - 粘贴小红书Cookie
   - 点击"保存Cookie"

2. **下载视频**
   - 访问"视频下载"标签页
   - 输入视频链接
   - 选择画质
   - 点击"创建下载任务"

3. **管理任务**
   - 访问"任务管理"标签页
   - 查看所有下载任务
   - 暂停/继续/删除任务

4. **收藏夹管理**
   - 访问"收藏夹"标签页
   - 添加收藏夹
   - 同步视频列表
   - 批量下载

### 方式二: API调用

#### 创建下载任务

```bash
curl -X POST "http://localhost:8000/api/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.xiaohongshu.com/explore/xxxx",
    "quality": "hd"
  }'
```

#### 启动任务

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/start"
```

#### 查看任务列表

```bash
curl "http://localhost:8000/api/tasks/"
```

#### 获取视频信息

```bash
curl "http://localhost:8000/api/videos/info?url=https://www.xiaohongshu.com/explore/xxxx"
```

## 📁 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置文件
│   ├── database.py             # 数据库配置
│   ├── models.py               # 数据模型
│   ├── schemas.py              # Pydantic 模型
│   ├── routers/                # API 路由
│   │   ├── auth.py            # 认证路由
│   │   ├── tasks.py           # 任务管理路由
│   │   ├── videos.py          # 视频信息路由
│   │   └── favorites.py       # 收藏夹路由
│   ├── services/               # 业务逻辑层
│   │   ├── xiaohongshu_api.py # 小红书API封装
│   │   ├── downloader.py      # 下载服务
│   │   └── task_manager.py    # 任务管理服务
│   └── static/                 # 静态文件
│       └── index.html         # Web界面
├── downloads/                  # 下载目录
├── requirements.txt            # 依赖列表
├── start.sh                    # 启动脚本
└── README.md                   # 项目说明
```

## ⚙️ 配置说明

### 环境变量

创建 `.env` 文件进行配置:

```env
# 应用配置
APP_NAME=小红书视频下载工具
APP_VERSION=1.0.0
DEBUG=true

# 数据库配置
DATABASE_URL=sqlite:///./xiaohongshu_downloader.db

# 下载配置
DOWNLOAD_DIR=./downloads
MAX_CONCURRENT_DOWNLOADS=3
CHUNK_SIZE=1048576
RETRY_TIMES=3
TIMEOUT=30

# Cookie存储路径
COOKIE_FILE=./cookies.json
```

### 下载配置

- `DOWNLOAD_DIR`: 下载文件保存目录
- `MAX_CONCURRENT_DOWNLOADS`: 最大并发下载数
- `CHUNK_SIZE`: 下载块大小(字节)
- `RETRY_TIMES`: 下载失败重试次数
- `TIMEOUT`: 请求超时时间(秒)

## 🔧 开发说明

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black app/
```

### 代码检查

```bash
ruff check app/
```

## 📝 API文档

启动服务后访问以下地址查看完整API文档:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

#### 任务管理
- `POST /api/tasks/` - 创建下载任务
- `GET /api/tasks/` - 获取任务列表
- `GET /api/tasks/{task_id}` - 获取任务详情
- `POST /api/tasks/{task_id}/start` - 启动任务
- `POST /api/tasks/{task_id}/pause` - 暂停任务
- `POST /api/tasks/{task_id}/resume` - 恢复任务
- `POST /api/tasks/{task_id}/stop` - 停止任务
- `POST /api/tasks/{task_id}/retry` - 重试任务
- `DELETE /api/tasks/{task_id}` - 删除任务

#### 视频信息
- `GET /api/videos/info` - 获取视频信息
- `GET /api/videos/download-url` - 获取下载链接
- `GET /api/videos/check-valid` - 检查视频有效性

#### 用户认证
- `POST /api/auth/login` - Cookie登录
- `POST /api/auth/validate` - 验证Cookie
- `GET /api/auth/current` - 获取当前用户
- `DELETE /api/auth/logout` - 登出

#### 收藏夹管理
- `POST /api/favorites/` - 创建收藏夹
- `GET /api/favorites/` - 获取收藏夹列表
- `GET /api/favorites/{favorite_id}` - 获取收藏夹详情
- `POST /api/favorites/{favorite_id}/sync` - 同步收藏夹
- `GET /api/favorites/{favorite_id}/videos` - 获取视频列表
- `POST /api/favorites/{favorite_id}/check-invalid` - 检测失效视频
- `POST /api/favorites/{favorite_id}/download-all` - 批量下载
- `DELETE /api/favorites/{favorite_id}` - 删除收藏夹

## ⚠️ 注意事项

1. **Cookie获取**
   - 打开浏览器,访问小红书官网
   - 登录账号
   - F12打开开发者工具
   - Network标签页查看请求头中的Cookie
   - 复制完整Cookie字符串

2. **下载限制**
   - 部分视频可能需要登录才能下载
   - 建议配置Cookie以获得完整功能
   - 遵守小红书的使用条款

3. **存储空间**
   - 确保有足够的磁盘空间
   - 定期清理下载目录

4. **网络要求**
   - 稳定的网络连接
   - 建议使用高速网络以提高下载速度

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者!

## 📞 联系方式

如有问题或建议,请提交 Issue。

---

**⚠️ 免责声明**: 本工具仅供学习交流使用,请勿用于商业用途。使用本工具下载视频时,请遵守相关法律法规和小红书的用户协议。
