# 视频URL提取失败问题修复指南

## 问题描述

当您看到以下错误消息时：
- "未能提取视频URL，所有方法均失败"
- "下载任务失败: 无法获取下载链接"

这意味着系统无法从小红书页面中提取视频下载链接。

## 快速解决方案

### 步骤1: 使用调试脚本诊断问题

运行增强的调试脚本来分析问题：

```bash
python debug_video_extraction.py "你的视频URL"
```

例如：
```bash
python debug_video_extraction.py "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"
```

### 步骤2: 查看诊断报告

脚本会自动：
1. ✅ 提取视频ID
2. ✅ 下载并分析页面HTML
3. ✅ 解析`__INITIAL_STATE__`JSON数据
4. ✅ 显示数据结构和可用字段
5. ✅ 生成详细的诊断报告

诊断文件保存在 `/tmp/xiaohongshu_debug/` 目录：
- `{video_id}_page.html` - 原始HTML页面
- `{video_id}_initial_state.json` - 提取的JSON数据
- `{video_id}_result.json` - 解析结果
- `{video_id}_diagnostic_report.txt` - 诊断报告

### 步骤3: 查看调试输出

调试脚本会显示详细的数据结构信息：
```
📝 笔记 6909e6c1000000000300ea0e:
   类型: video
   标题: 视频标题
   包含video: True
   video的键: ['media', 'consumer', 'cover', 'duration', 'width', 'height', ...]
   media.stream.h264[0]的键: ['masterUrl', 'backupUrls', 'url', ...]
```

## 已实现的修复

### 修复内容

1. **多路径数据探测**
   - 尝试3种不同的JSON数据路径
   - 自动适配小红书页面结构变化

2. **5种视频URL提取方法**
   - 方法1: `media.stream.h264[0].masterUrl`
   - 方法2: `media.stream.h264[0].backupUrls[0]`
   - 方法3: `video.consumer.originVideoKey` (构建CDN URL)
   - 方法4: `video.masterUrl`
   - 方法5: `video.playAddr` / `video.videoUrl` (新增)

3. **改进的JSON解析**
   - 处理JavaScript的`undefined`值
   - 移除JSON尾部逗号
   - 更健壮的正则匹配

4. **详细的调试日志**
   - 每一步都有日志输出
   - 显示尝试的方法和结果
   - 输出数据结构的键以便分析

## 常见问题排查

### Q1: 仍然无法提取视频URL？

**检查调试输出中的video对象键**：
```bash
# 查看JSON数据
cat /tmp/xiaohongshu_debug/{video_id}_initial_state.json | grep -A 20 "video"
```

如果video对象中有新的字段名，请在GitHub提issue报告。

### Q2: 提示"未找到 __INITIAL_STATE__ 数据"？

可能原因：
1. 网络问题，无法访问小红书页面
2. 小红书页面结构发生重大变化
3. 需要登录才能访问该视频

**解决方法**：
- 检查网络连接
- 尝试配置Cookie（如果需要登录）
- 查看HTML文件确认页面内容

### Q3: 如何配置Cookie？

如果视频需要登录才能访问：

```python
from app.services.xiaohongshu_api import XiaohongshuAPI

# 方法1: JSON格式
api = XiaohongshuAPI(cookies='{"a1":"xxx", "webId":"yyy"}')

# 方法2: 键值对格式
api = XiaohongshuAPI(cookies='a1=xxx; webId=yyy')

# 或者后续设置
api.set_cookies('a1=xxx; webId=yyy')
```

### Q4: 视频类型不是video？

有些笔记类型可能是图文混合内容：
- 检查诊断输出中的"类型"字段
- 确认该笔记确实包含视频
- 图文笔记可能没有video对象

## 技术细节

### 数据结构探测逻辑

```python
# 优先级1: noteDetailMap路径
state_data['note']['noteDetailMap'][note_id]['note']

# 优先级2: 直接note路径
state_data['note']['note']

# 优先级3: noteDetail路径
state_data['note']['noteDetail']['note']
```

### 视频URL提取优先级

```python
if video:
    # 1. 尝试h264流
    url = video['media']['stream']['h264'][0]['masterUrl']

    # 2. 尝试备份URL
    url = video['media']['stream']['h264'][0]['backupUrls'][0]

    # 3. 构建CDN URL
    url = f"https://sns-video-bd.xhscdn.com/{video['consumer']['originVideoKey']}"

    # 4. 直接masterUrl
    url = video['masterUrl']

    # 5. 其他字段
    url = video['playAddr'] or video['videoUrl']
```

## 报告问题

如果问题仍未解决，请提供以下信息：

1. 视频URL
2. 调试脚本的完整输出
3. `/tmp/xiaohongshu_debug/` 目录中的文件（特别是JSON文件）
4. 错误信息和堆栈跟踪

GitHub Issues: [在这里创建issue]

## 相关文件

- `app/services/xiaohongshu_api.py` - 核心提取逻辑
- `debug_video_extraction.py` - 增强调试脚本
- `test_video_url.py` - 基础测试脚本
- `FIX_VIDEO_DOWNLOAD.md` - 详细修复文档
