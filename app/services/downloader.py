"""
视频下载服务
"""
import asyncio
import httpx
import os
import time
from typing import Optional, Callable
from pathlib import Path
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class VideoDownloader:
    """视频下载器"""

    def __init__(self):
        self.download_dir = Path(settings.DOWNLOAD_DIR)
        self.chunk_size = settings.CHUNK_SIZE
        self.retry_times = settings.RETRY_TIMES
        self.timeout = settings.TIMEOUT
        self._stop_flag = False

    async def download_video(
        self,
        url: str,
        file_path: str,
        progress_callback: Optional[Callable] = None,
        resume: bool = True,
    ) -> bool:
        """
        下载视频
        Args:
            url: 视频URL
            file_path: 保存路径
            progress_callback: 进度回调函数 callback(downloaded, total, speed)
            resume: 是否支持断点续传
        Returns:
            是否下载成功
        """
        self._stop_flag = False
        temp_file = f"{file_path}.tmp"

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 检查是否有未完成的下载
        downloaded_size = 0
        if resume and os.path.exists(temp_file):
            downloaded_size = os.path.getsize(temp_file)
            logger.info(f"断点续传: 已下载 {downloaded_size} 字节")

        retry_count = 0
        while retry_count < self.retry_times:
            try:
                # 设置请求头支持断点续传
                headers = {}
                if downloaded_size > 0:
                    headers['Range'] = f'bytes={downloaded_size}-'

                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    async with client.stream('GET', url, headers=headers) as response:
                        # 检查是否支持断点续传
                        if response.status_code not in [200, 206]:
                            logger.warning(f"服务器返回状态码: {response.status_code}")
                            if response.status_code == 416:  # Range Not Satisfiable
                                # 可能文件已下载完成
                                if os.path.exists(temp_file):
                                    os.rename(temp_file, file_path)
                                return True
                            response.raise_for_status()

                        # 获取文件总大小
                        content_length = response.headers.get('content-length')
                        if content_length:
                            total_size = int(content_length) + downloaded_size
                        else:
                            total_size = 0

                        # 开始下载
                        mode = 'ab' if downloaded_size > 0 else 'wb'
                        start_time = time.time()
                        last_update_time = start_time

                        with open(temp_file, mode) as f:
                            async for chunk in response.aiter_bytes(chunk_size=self.chunk_size):
                                if self._stop_flag:
                                    logger.info("下载已停止")
                                    return False

                                f.write(chunk)
                                downloaded_size += len(chunk)

                                # 更新进度
                                current_time = time.time()
                                if current_time - last_update_time >= 0.5:  # 每0.5秒更新一次
                                    elapsed_time = current_time - start_time
                                    speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0

                                    if progress_callback:
                                        await progress_callback(downloaded_size, total_size, speed)

                                    last_update_time = current_time

                        # 下载完成,重命名文件
                        if os.path.exists(temp_file):
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            os.rename(temp_file, file_path)

                        logger.info(f"下载完成: {file_path}")
                        return True

            except Exception as e:
                retry_count += 1
                logger.error(f"下载失败 (尝试 {retry_count}/{self.retry_times}): {e}")

                if retry_count < self.retry_times:
                    await asyncio.sleep(2 ** retry_count)  # 指数退避
                else:
                    logger.error(f"下载失败,已达到最大重试次数: {url}")
                    return False

        return False

    def stop_download(self):
        """停止当前下载"""
        self._stop_flag = True

    async def download_multi_parts(
        self,
        urls: list,
        output_dir: str,
        progress_callback: Optional[Callable] = None,
    ) -> list:
        """
        下载多个分P视频
        Args:
            urls: URL列表 [(part_num, url), ...]
            output_dir: 输出目录
            progress_callback: 进度回调
        Returns:
            下载成功的文件列表
        """
        os.makedirs(output_dir, exist_ok=True)

        tasks = []
        for part_num, url in urls:
            file_name = f"part_{part_num:02d}.mp4"
            file_path = os.path.join(output_dir, file_name)
            tasks.append(self.download_video(url, file_path, progress_callback))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 返回成功下载的文件
        success_files = []
        for i, (part_num, url) in enumerate(urls):
            if results[i] is True:
                file_name = f"part_{part_num:02d}.mp4"
                success_files.append(os.path.join(output_dir, file_name))

        return success_files

    def get_downloaded_size(self, file_path: str) -> int:
        """获取已下载文件大小"""
        temp_file = f"{file_path}.tmp"
        if os.path.exists(temp_file):
            return os.path.getsize(temp_file)
        elif os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    def clean_temp_files(self, file_path: str):
        """清理临时文件"""
        temp_file = f"{file_path}.tmp"
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.info(f"已清理临时文件: {temp_file}")
            except Exception as e:
                logger.error(f"清理临时文件失败: {e}")

    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            return {
                'exists': True,
                'size': stat.st_size,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime,
            }
        return {'exists': False}
