# 修复小红书视频下载链接提取问题

## 问题描述

用户报告在尝试下载包含视频的小红书链接时出现错误：
- 测试URL: `https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e`
- 错误信息: "无法获取下载链接"

## 问题分析

经过分析，发现问题出在 `app/services/xiaohongshu_api.py` 的视频页面解析逻辑中：

1. **正则表达式匹配不够健壮**
   - 原有的单一正则模式可能无法匹配所有情况下的 `__INITIAL_STATE__` 数据
   - 小红书的页面结构可能有多种变体

2. **视频URL提取路径单一**
   - 原来只尝试从 `video.media.stream.h264[0].masterUrl` 获取
   - 如果这个路径不存在，就会返回空字符串

3. **缺少详细的调试信息**
   - 难以定位具体是哪个环节出了问题

## 修复内容

### 1. 改进正则表达式匹配 (`app/services/xiaohongshu_api.py:102-107`)

增加了多个正则模式，依次尝试匹配：
```python
state_patterns = [
    r'<script>window\.__INITIAL_STATE__=({.*?})</script>',
    r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>',
    r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;',
    r'__INITIAL_STATE__\s*=\s*({[\s\S]*?})\s*(?:</script>|;)',
]
```

### 2. 增加多种视频URL提取方法 (`app/services/xiaohongshu_api.py:138-174`)

现在支持以下多种提取方式：

**方式1**: 从 `media.stream.h264` 获取
- 尝试 `masterUrl`
- 如果失败，尝试 `backupUrls[0]`
- 如果还失败，尝试直接的 `url` 字段

**方式2**: 从 `video.consumer.originVideoKey` 构建
- 拼接CDN域名: `https://sns-video-bd.xhscdn.com/{originVideoKey}`

**方式3**: 从 `video.masterUrl` 直接获取

### 3. 添加调试模式 (`app/services/xiaohongshu_api.py:50-103`)

`get_video_info()` 方法现在支持 `debug=True` 参数：
- 保存原始HTML页面到 `/tmp/xiaohongshu_debug/{video_id}_page.html`
- 保存提取的JSON数据到 `/tmp/xiaohongshu_debug/{video_id}_initial_state.json`
- 保存解析结果到 `/tmp/xiaohongshu_debug/{video_id}_result.json`

### 4. 增强日志记录

添加了详细的日志输出，便于排查问题：
- 记录视频ID提取
- 记录页面请求状态
- 记录正则匹配结果
- 记录每种URL提取方法的尝试情况

## 测试方法

### 方法1: 使用API测试

启动服务后，访问API端点测试：

```bash
# 启动服务
./start.sh

# 测试获取视频信息
curl "http://localhost:8000/api/videos/info?url=https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"
```

### 方法2: 使用测试脚本

```bash
# 方式1: 使用完整测试脚本
python test_download.py

# 方式2: 使用调试测试脚本
python test_video_url.py "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"

# 查看调试输出
ls -la /tmp/xiaohongshu_debug/
```

### 方法3: 通过Web界面测试

1. 启动服务: `./start.sh`
2. 访问: `http://localhost:8000`
3. 在"视频下载"标签页输入URL
4. 点击"创建下载任务"
5. 查看任务状态

## 预期效果

修复后，系统能够：

1. ✅ 正确提取视频ID
2. ✅ 成功匹配页面中的 `__INITIAL_STATE__` 数据
3. ✅ 通过多种方式尝试提取视频下载链接
4. ✅ 提供详细的日志和调试信息
5. ✅ 在某一种方法失败时自动尝试其他方法

## 注意事项

1. **Cookie要求**
   - 某些视频可能需要登录才能访问
   - 如果仍然无法获取链接，请尝试配置Cookie

2. **网络要求**
   - 确保可以正常访问小红书网站
   - 如果页面无法访问，所有解析都会失败

3. **页面结构变化**
   - 小红书可能会更新页面结构
   - 如果所有方法都失败，可能需要更新解析逻辑
   - 使用调试模式可以帮助分析新的页面结构

## 相关文件

- `app/services/xiaohongshu_api.py` - 主要修复文件
- `test_video_url.py` - 新增的调试测试脚本
- `test_parse_only.py` - 简单的解析测试脚本

## 下一步

如果问题仍然存在：

1. 开启调试模式运行测试
2. 查看保存的HTML和JSON文件
3. 分析实际的数据结构
4. 根据实际结构调整解析代码

## 更新历史

### 2025-11-15 (第二次修复)

**问题**: 用户反馈"未能提取视频URL，所有方法均失败"，说明之前的修复不够完整。

**新增修复内容**:

1. **增强数据路径探测** (`app/services/xiaohongshu_api.py:169-212`)
   - 新增多个数据路径尝试:
     - 路径1: `state_data.note.noteDetailMap[note_id].note` (原有)
     - 路径2: `state_data.note.note` (新增，直接路径)
     - 路径3: `state_data.note.noteDetail` (新增)
   - 智能匹配：优先查找匹配的video_id或包含video的笔记

2. **改进JSON清理逻辑** (第143-146行)
   - 使用正则表达式更彻底地清理JavaScript特有值
   - 移除尾部逗号避免JSON解析错误
   - 处理 `undefined` 关键字

3. **新增视频URL提取方法** (第260-269行)
   - 方式4: 从 `video.playAddr` 获取
   - 方式5: 从 `video.videoUrl` 获取

4. **增强调试信息** (第204-212, 223, 227, 275-276行)
   - 输出数据结构的关键路径和键
   - 显示找到的note类型和video对象
   - 输出h264对象的所有可用字段
   - 输出video对象的所有可用字段

5. **新增增强调试脚本** (`debug_video_extraction.py`)
   - 分步骤显示提取过程
   - 自动分析JSON数据结构
   - 生成详细的诊断报告
   - 提供明确的排查建议

6. **改进标题提取** (第282行)
   - 如果没有title字段，使用desc的前50字符作为标题

**使用新的调试脚本**:
```bash
python debug_video_extraction.py "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"

# 查看详细的数据结构分析和诊断报告
ls -la /tmp/xiaohongshu_debug/
```

### 2025-11-15 (初次修复)
