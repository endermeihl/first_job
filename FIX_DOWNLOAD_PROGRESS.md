# 下载进度卡在0%问题的修复说明

## 问题描述

创建下载任务后，调用 `/api/tasks/{task_id}/start` 启动下载，任务状态变为 `downloading`，但进度一直保持在 0%，无法正常更新。

## 根本原因

**数据库Session生命周期管理问题**

在原始代码中，`tasks.py` 的 `start_task` 路由使用了 FastAPI 的后台任务机制：

```python
@router.post("/{task_id}/start")
async def start_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)  # ← 请求级别的session
):
    # 将请求的db session传递给后台任务
    background_tasks.add_task(task_manager.start_task, db, task_id, cookies)
    return {"code": 200, "message": "任务已启动"}
```

问题出在：

1. **Session的生命周期**：`get_db()` 依赖项创建的数据库Session是请求级别的
2. **请求结束后关闭**：当HTTP响应返回后，`get_db()` 的 `finally` 块会关闭这个Session
3. **后台任务Session失效**：后台下载任务尝试使用已关闭的Session更新进度时失败
4. **进度无法更新**：导致数据库无法写入进度信息，进度一直停留在0%

## 解决方案

### 核心思路

**后台任务应该创建并管理自己的数据库Session，而不是复用请求的Session。**

### 代码修改

#### 1. 添加包装函数 `_download_task_wrapper`

在 `app/services/task_manager.py` 中添加新方法：

```python
async def _download_task_wrapper(self, task_id: str, cookies: Optional[str] = None):
    """
    下载任务包装器 - 创建独立的数据库会话
    """
    from ..database import SessionLocal

    # 为后台任务创建新的数据库会话
    db = SessionLocal()
    try:
        # 查询任务
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return

        # 执行下载
        await self._download_task(db, task, cookies)
    finally:
        db.close()  # 确保session被正确关闭
```

#### 2. 修改 `start_task` 方法

```python
async def start_task(self, db: Session, task_id: str, cookies: Optional[str] = None):
    # ... 验证和状态更新代码 ...

    task.status = TaskStatus.DOWNLOADING
    task.started_at = datetime.now()
    db.commit()

    # 创建下载任务 - 只传递task_id，不传递session对象
    download_task = asyncio.create_task(
        self._download_task_wrapper(task_id, cookies)  # ← 使用包装器
    )
    self.active_tasks[task_id] = download_task
```

### 修改文件清单

- `app/services/task_manager.py`:
  - 新增 `_download_task_wrapper()` 方法
  - 修改 `start_task()` 调用逻辑
- `test_download.py`: 添加完整的下载功能测试脚本
- `test_basic_download.py`: 添加基础下载器测试脚本

## 技术细节

### Session管理对比

**修改前（错误）**:
```
HTTP请求 → get_db()创建Session → 传递给后台任务 → HTTP响应返回
                                              ↓
                                    Session被关闭 (get_db的finally块)
                                              ↓
                                    后台任务尝试使用 → ❌ Session已关闭
```

**修改后（正确）**:
```
HTTP请求 → get_db()创建Session1 → 更新任务状态 → HTTP响应返回 → Session1关闭
                                           ↓
                      后台任务 → 创建新的Session2 → 执行下载和进度更新 → Session2关闭 ✅
```

### 为什么这样修复有效？

1. **独立生命周期**：每个后台任务拥有自己的Session，不受HTTP请求生命周期影响
2. **正确的资源管理**：Session在后台任务内部创建和销毁，确保资源正确清理
3. **事务隔离**：每个任务的数据库操作相互独立，不会互相干扰
4. **异步安全**：SessionLocal每次调用都创建新实例，线程/协程安全

## 测试方法

### 1. 使用测试脚本

```bash
# 测试完整下载流程（需要提供小红书URL）
python3 test_download.py

# 测试基础下载器功能
python3 test_basic_download.py
```

### 2. 通过API测试

```bash
# 1. 创建任务
curl -X POST "http://localhost:8000/api/tasks/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.xiaohongshu.com/explore/YOUR_VIDEO_ID",
    "quality": "hd"
  }'

# 记录返回的 task_id

# 2. 启动下载
curl -X POST "http://localhost:8000/api/tasks/{task_id}/start"

# 3. 查询进度（应该看到进度逐渐增加）
curl "http://localhost:8000/api/tasks/{task_id}"
```

### 3. 观察进度更新

成功修复后，你应该看到：

```json
{
  "task_id": "xxx",
  "status": "downloading",
  "progress": 15.6,        ← 进度会持续更新
  "downloaded_size": 1048576,
  "total_size": 6710886,
  "speed": 512.5           ← 下载速度(KB/s)
}
```

## 相关API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tasks/` | POST | 创建下载任务 |
| `/api/tasks/{task_id}/start` | POST | **启动下载** (已修复) |
| `/api/tasks/{task_id}` | GET | 查询任务进度 |
| `/api/tasks/{task_id}/pause` | POST | 暂停下载 |
| `/api/tasks/{task_id}/resume` | POST | 恢复下载 |
| `/api/tasks/{task_id}/stop` | POST | 停止下载 |
| `/api/tasks/{task_id}/retry` | POST | 重试失败任务 |

## 其他注意事项

### Cookie要求

某些视频可能需要登录才能下载，需要提供有效的Cookie：

```bash
curl -X POST "http://localhost:8000/api/tasks/{task_id}/start" \
  -H "Content-Type: application/json" \
  -d '{"cookies": "your_cookie_string"}'
```

### 并发下载

配置项 `MAX_CONCURRENT_DOWNLOADS` 控制最大并发下载数量（默认3个）：

```python
# app/config.py
MAX_CONCURRENT_DOWNLOADS = 3
```

### 断点续传

下载器支持断点续传，中断后可以使用 `/resume` 端点继续下载。

## 部署建议

1. **重启服务**：修复后需要重启FastAPI服务以加载新代码
   ```bash
   # 如果使用start.sh
   ./start.sh

   # 或直接使用uvicorn
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **清理旧任务**：建议清理状态为 `downloading` 但实际未下载的旧任务
   ```bash
   # 删除所有下载中的任务
   curl -X GET "http://localhost:8000/api/tasks/?status=downloading"
   # 然后逐个删除
   curl -X DELETE "http://localhost:8000/api/tasks/{task_id}"
   ```

3. **监控日志**：观察应用日志确认下载任务正常运行
   ```bash
   # 查看日志
   tail -f /path/to/logfile
   ```

## 总结

此修复解决了FastAPI后台任务中常见的数据库Session管理问题，确保异步下载任务能够正常更新进度到数据库。核心原则是：**每个长期运行的后台任务应该管理自己的数据库Session，而不是复用请求级别的Session**。

---

**修复版本**: v1.0.1
**修复日期**: 2025-11-15
**影响范围**: 下载进度追踪功能
