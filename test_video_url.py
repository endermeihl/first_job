#!/usr/bin/env python3
"""
测试特定视频URL的下载链接提取
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/user/first_job')

from app.services.xiaohongshu_api import XiaohongshuAPI


async def test_video_url(video_url: str):
    """测试视频URL"""
    print(f"\n{'='*80}")
    print("测试视频链接提取")
    print(f"{'='*80}")
    print(f"视频URL: {video_url}")
    print(f"{'='*80}\n")

    try:
        # 创建API实例
        api = XiaohongshuAPI()

        # 获取视频信息（开启调试模式）
        print("正在获取视频信息...")
        video_info = await api.get_video_info(video_url, debug=True)

        print(f"\n{'='*80}")
        print("视频信息")
        print(f"{'='*80}")
        print(f"视频ID: {video_info.get('video_id')}")
        print(f"标题: {video_info.get('title')}")
        print(f"作者: {video_info.get('author')}")
        print(f"时长: {video_info.get('duration')}秒")
        print(f"分辨率: {video_info.get('width')}x{video_info.get('height')}")
        print(f"封面URL: {video_info.get('cover_url')[:80] if video_info.get('cover_url') else 'N/A'}...")
        print(f"\n视频URL: {video_info.get('video_url') or '未找到视频链接 ❌'}")

        if video_info.get('video_url'):
            print(f"\n✅ 成功提取到视频下载链接！")
            print(f"\n完整链接:")
            print(video_info.get('video_url'))
        else:
            print(f"\n❌ 未能提取到视频下载链接")
            print(f"\n请查看调试文件以了解详情:")
            video_id = video_info.get('video_id')
            print(f"  - HTML: /tmp/xiaohongshu_debug/{video_id}_page.html")
            print(f"  - JSON: /tmp/xiaohongshu_debug/{video_id}_initial_state.json")
            print(f"  - 结果: /tmp/xiaohongshu_debug/{video_id}_result.json")

        print(f"\n{'='*80}\n")

        return video_info

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """主函数"""
    # 使用用户提供的URL
    default_url = "https://www.xiaohongshu.com/explore/6909e6c1000000000300ea0e"

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        print(f"使用默认测试URL: {default_url}")
        test_url = default_url

    await test_video_url(test_url)


if __name__ == "__main__":
    asyncio.run(main())
