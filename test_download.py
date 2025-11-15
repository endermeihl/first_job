#!/usr/bin/env python3
"""
下载功能测试脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/user/first_job')

from app.services.xiaohongshu_api import XiaohongshuAPI
from app.services.downloader import VideoDownloader
from app.config import settings


async def test_video_info(video_url: str):
    """测试获取视频信息"""
    print(f"\n{'='*60}")
    print("测试1: 获取视频信息")
    print(f"{'='*60}")
    print(f"视频URL: {video_url}")

    try:
        api = XiaohongshuAPI()
        video_info = await api.get_video_info(video_url)

        print(f"\n✅ 成功获取视频信息:")
        print(f"  - 视频ID: {video_info.get('video_id')}")
        print(f"  - 标题: {video_info.get('title')}")
        print(f"  - 作者: {video_info.get('author')}")
        print(f"  - 时长: {video_info.get('duration')}秒")
        print(f"  - 分辨率: {video_info.get('width')}x{video_info.get('height')}")
        print(f"  - 下载URL: {video_info.get('video_url')[:80] if video_info.get('video_url') else '未找到'}...")

        return video_info
    except Exception as e:
        print(f"\n❌ 获取视频信息失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_download_url(video_id: str):
    """测试获取下载链接"""
    print(f"\n{'='*60}")
    print("测试2: 获取下载链接")
    print(f"{'='*60}")
    print(f"视频ID: {video_id}")

    try:
        api = XiaohongshuAPI()
        download_url = await api.get_download_url(video_id, 'hd')

        if download_url:
            print(f"\n✅ 成功获取下载链接:")
            print(f"  - URL: {download_url[:100]}...")
            return download_url
        else:
            print("\n❌ 未能获取下载链接")
            return None
    except Exception as e:
        print(f"\n❌ 获取下载链接失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_download(download_url: str, file_path: str):
    """测试下载功能"""
    print(f"\n{'='*60}")
    print("测试3: 下载视频")
    print(f"{'='*60}")
    print(f"下载URL: {download_url[:80]}...")
    print(f"保存路径: {file_path}")

    try:
        downloader = VideoDownloader()

        # 进度回调
        progress_data = {'last_progress': 0}

        async def progress_callback(downloaded, total, speed):
            progress = (downloaded / total * 100) if total > 0 else 0
            # 每10%更新一次显示
            if progress - progress_data['last_progress'] >= 10:
                print(f"  进度: {progress:.1f}% ({downloaded}/{total} bytes, {speed/1024:.1f} KB/s)")
                progress_data['last_progress'] = progress

        success = await downloader.download_video(
            url=download_url,
            file_path=file_path,
            progress_callback=progress_callback,
            resume=True
        )

        if success:
            file_size = os.path.getsize(file_path)
            print(f"\n✅ 下载成功!")
            print(f"  - 文件大小: {file_size / (1024*1024):.2f} MB")
            print(f"  - 文件路径: {file_path}")
            return True
        else:
            print("\n❌ 下载失败")
            return False

    except Exception as e:
        print(f"\n❌ 下载过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_url_accessibility(url: str):
    """测试URL可访问性"""
    print(f"\n{'='*60}")
    print("测试0: 检查URL可访问性")
    print(f"{'='*60}")

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.head(url)
            print(f"URL状态码: {response.status_code}")
            if response.status_code == 200:
                content_length = response.headers.get('content-length')
                if content_length:
                    print(f"文件大小: {int(content_length) / (1024*1024):.2f} MB")
                print(f"✅ URL可访问")
                return True
            else:
                print(f"❌ URL不可访问 (状态码: {response.status_code})")
                return False
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("小红书视频下载功能测试")
    print("="*60)

    # 测试URL - 使用用户提供的URL或默认测试URL
    test_url = input("\n请输入小红书视频URL (按回车使用默认测试): ").strip()

    if not test_url:
        print("\n⚠️  未提供测试URL，无法继续测试")
        print("请提供一个小红书视频URL，格式如: https://www.xiaohongshu.com/explore/xxxxxxxxx")
        return

    # 第一步: 获取视频信息
    video_info = await test_video_info(test_url)
    if not video_info:
        print("\n❌ 测试终止: 无法获取视频信息")
        return

    video_id = video_info.get('video_id')
    if not video_id:
        print("\n❌ 测试终止: 无法提取视频ID")
        return

    # 第二步: 获取下载链接
    download_url = video_info.get('video_url')
    if not download_url:
        print("\n尝试通过API获取下载链接...")
        download_url = await test_download_url(video_id)

    if not download_url:
        print("\n❌ 测试终止: 无法获取下载链接")
        return

    # 第三步: 测试URL可访问性
    url_accessible = await test_url_accessibility(download_url)
    if not url_accessible:
        print("\n⚠️  下载URL不可访问，可能需要Cookie认证")
        print("请通过登录方式获取Cookie后重试")
        return

    # 第四步: 测试下载
    file_path = f"/home/user/first_job/downloads/test_{video_id}.mp4"
    success = await test_download(download_url, file_path)

    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    print(f"获取视频信息: {'✅ 通过' if video_info else '❌ 失败'}")
    print(f"获取下载链接: {'✅ 通过' if download_url else '❌ 失败'}")
    print(f"URL可访问性: {'✅ 通过' if url_accessible else '❌ 失败'}")
    print(f"下载视频: {'✅ 通过' if success else '❌ 失败'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
