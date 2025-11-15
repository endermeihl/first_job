#!/usr/bin/env python3
"""
基础下载功能测试 - 使用公开测试文件
"""
import asyncio
import sys
import os

sys.path.insert(0, '/home/user/first_job')

from app.services.downloader import VideoDownloader


async def test_basic_download():
    """测试基础下载功能"""
    print("="*60)
    print("测试: 基础下载功能")
    print("="*60)

    # 使用一个小的公开测试视频
    test_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    file_path = "/home/user/first_job/downloads/test_basic.mp4"

    print(f"\n测试URL: {test_url}")
    print(f"保存路径: {file_path}\n")

    try:
        downloader = VideoDownloader()

        # 进度追踪
        async def progress_callback(downloaded, total, speed):
            progress = (downloaded / total * 100) if total > 0 else 0
            print(f"\r进度: {progress:.1f}% | {downloaded}/{total} bytes | {speed/1024:.1f} KB/s", end='', flush=True)

        print("开始下载...")
        success = await downloader.download_video(
            url=test_url,
            file_path=file_path,
            progress_callback=progress_callback,
            resume=True
        )

        print("\n")  # 换行

        if success and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ 下载成功!")
            print(f"   文件大小: {file_size / (1024*1024):.2f} MB")
            print(f"   文件路径: {file_path}")
            return True
        else:
            print("❌ 下载失败")
            return False

    except Exception as e:
        print(f"\n❌ 下载出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_basic_download())
    sys.exit(0 if result else 1)
