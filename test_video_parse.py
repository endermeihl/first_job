"""
测试小红书视频链接解析
"""
import httpx
import json
import re
import asyncio

async def test_video_url():
    url = "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")

        # 保存HTML到文件
        with open('/tmp/xiaohongshu_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("已保存HTML到 /tmp/xiaohongshu_page.html")

        # 查找 __INITIAL_STATE__
        state_pattern = r'<script>window\.__INITIAL_STATE__=({.*?})</script>'
        match = re.search(state_pattern, response.text, re.DOTALL)

        if match:
            print("\n找到 __INITIAL_STATE__")
            state_data = match.group(1).replace(':undefined', ':null')

            # 保存JSON数据
            with open('/tmp/initial_state.json', 'w', encoding='utf-8') as f:
                f.write(state_data)
            print("已保存 JSON 到 /tmp/initial_state.json")

            # 尝试解析
            try:
                data = json.loads(state_data)
                print("\nJSON 解析成功")

                # 查找视频相关数据
                note_data = data.get('note', {}).get('noteDetailMap', {})
                print(f"\nnoteDetailMap 包含 {len(note_data)} 个条目")

                for note_id, note_info in note_data.items():
                    print(f"\n笔记 ID: {note_id}")
                    note = note_info.get('note', {})
                    print(f"标题: {note.get('title', 'N/A')}")
                    print(f"类型: {note.get('type', 'N/A')}")

                    video = note.get('video', {})
                    if video:
                        print("\n视频数据结构:")
                        print(json.dumps(video, indent=2, ensure_ascii=False)[:1000])

                        # 尝试提取视频URL
                        media = video.get('media', {})
                        stream = media.get('stream', {})
                        h264_list = stream.get('h264', [])

                        print(f"\nh264 列表长度: {len(h264_list)}")
                        if h264_list:
                            for idx, item in enumerate(h264_list):
                                print(f"\nh264[{idx}] 的键: {list(item.keys())}")
                                master_url = item.get('masterUrl', '')
                                backup_urls = item.get('backupUrls', [])
                                print(f"masterUrl: {master_url[:100] if master_url else 'N/A'}")
                                print(f"backupUrls 数量: {len(backup_urls)}")
                    else:
                        print("未找到视频数据")

            except json.JSONDecodeError as e:
                print(f"\nJSON 解析失败: {e}")
        else:
            print("\n未找到 __INITIAL_STATE__")

            # 尝试其他可能的模式
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'<script>\s*window\.__INITIAL_STATE__\s*=\s*(.*?)\s*</script>',
                r'__INITIAL_STATE__\s*=\s*({[\s\S]*?})\s*;',
            ]

            for i, pattern in enumerate(patterns):
                match = re.search(pattern, response.text, re.DOTALL)
                if match:
                    print(f"使用模式 {i+1} 找到匹配")
                    break

if __name__ == "__main__":
    asyncio.run(test_video_url())
