"""
任务管理服务
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from ..models import DownloadTask, TaskStatus, VideoQuality
from ..schemas import DownloadTaskCreate, DownloadTaskUpdate
from .xiaohongshu_api import XiaohongshuAPI
from .downloader import VideoDownloader
from ..config import settings
import logging
import os

logger = logging.getLogger(__name__)


class TaskManager:
    """任务管理器"""

    def __init__(self):
        self.downloader = VideoDownloader()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.xhs_api = XiaohongshuAPI()

    async def create_task(
        self,
        db: Session,
        task_data: DownloadTaskCreate,
        cookies: Optional[str] = None,
    ) -> DownloadTask:
        """
        创建下载任务
        Args:
            db: 数据库会话
            task_data: 任务数据
            cookies: Cookie字符串
        Returns:
            创建的任务
        """
        # 设置Cookie
        if cookies:
            self.xhs_api.set_cookies(cookies)

        # 获取视频信息
        try:
            video_info = await self.xhs_api.get_video_info(task_data.video_url)
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            video_info = {
                'video_id': None,
                'title': '未知',
                'author': '未知',
                'cover_url': None,
            }

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务
        db_task = DownloadTask(
            task_id=task_id,
            video_url=task_data.video_url,
            video_id=video_info.get('video_id'),
            title=video_info.get('title', '未知'),
            author=video_info.get('author', '未知'),
            cover_url=video_info.get('cover_url'),
            quality=task_data.quality,
            parts=task_data.parts,
            status=TaskStatus.PENDING,
            progress=0.0,
            downloaded_size=0,
            total_size=0,
            speed=0.0,
        )

        db.add(db_task)
        db.commit()
        db.refresh(db_task)

        return db_task

    async def start_task(self, db: Session, task_id: str, cookies: Optional[str] = None):
        """
        启动下载任务
        Args:
            db: 数据库会话
            task_id: 任务ID
            cookies: Cookie字符串
        """
        # 查询任务
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.status == TaskStatus.DOWNLOADING:
            raise ValueError(f"任务正在下载中: {task_id}")

        # 更新任务状态
        task.status = TaskStatus.DOWNLOADING
        task.started_at = datetime.now()
        db.commit()

        # 创建下载任务
        download_task = asyncio.create_task(
            self._download_task(db, task, cookies)
        )
        self.active_tasks[task_id] = download_task

    async def _download_task(self, db: Session, task: DownloadTask, cookies: Optional[str] = None):
        """
        执行下载任务
        """
        try:
            # 设置Cookie
            if cookies:
                self.xhs_api.set_cookies(cookies)

            # 获取下载链接
            download_url = await self.xhs_api.get_download_url(
                task.video_id or task.video_url,
                task.quality.value
            )

            if not download_url:
                raise ValueError("无法获取下载链接")

            # 构建文件路径
            safe_title = "".join(c for c in task.title if c.isalnum() or c in (' ', '-', '_')).strip()
            file_name = f"{safe_title}_{task.video_id}.mp4"
            file_path = os.path.join(settings.DOWNLOAD_DIR, file_name)

            task.file_path = file_path
            db.commit()

            # 进度回调
            async def progress_callback(downloaded, total, speed):
                task.downloaded_size = downloaded
                task.total_size = total
                task.speed = speed / 1024  # 转换为KB/s
                task.progress = (downloaded / total * 100) if total > 0 else 0
                db.commit()

            # 开始下载
            success = await self.downloader.download_video(
                url=download_url,
                file_path=file_path,
                progress_callback=progress_callback,
                resume=True,
            )

            if success:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.progress = 100.0
            else:
                task.status = TaskStatus.FAILED
                task.error_message = "下载失败"

            db.commit()

        except Exception as e:
            logger.error(f"下载任务失败: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1
            db.commit()

        finally:
            # 从活动任务中移除
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

    async def stop_task(self, db: Session, task_id: str):
        """
        停止下载任务
        Args:
            db: 数据库会话
            task_id: 任务ID
        """
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 停止下载
        self.downloader.stop_download()

        # 取消异步任务
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]

        # 更新状态
        task.status = TaskStatus.STOPPED
        db.commit()

    async def pause_task(self, db: Session, task_id: str):
        """
        暂停下载任务
        Args:
            db: 数据库会话
            task_id: 任务ID
        """
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 停止下载但保留临时文件
        self.downloader.stop_download()

        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]

        task.status = TaskStatus.PAUSED
        db.commit()

    async def resume_task(self, db: Session, task_id: str, cookies: Optional[str] = None):
        """
        恢复下载任务
        Args:
            db: 数据库会话
            task_id: 任务ID
            cookies: Cookie字符串
        """
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.status != TaskStatus.PAUSED:
            raise ValueError(f"任务未暂停,无法恢复: {task_id}")

        await self.start_task(db, task_id, cookies)

    def get_task(self, db: Session, task_id: str) -> Optional[DownloadTask]:
        """获取任务"""
        return db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()

    def get_tasks(
        self,
        db: Session,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DownloadTask]:
        """
        获取任务列表
        Args:
            db: 数据库会话
            status: 任务状态过滤
            skip: 跳过数量
            limit: 限制数量
        Returns:
            任务列表
        """
        query = db.query(DownloadTask)
        if status:
            query = query.filter(DownloadTask.status == status)
        return query.order_by(DownloadTask.created_at.desc()).offset(skip).limit(limit).all()

    def delete_task(self, db: Session, task_id: str) -> bool:
        """
        删除任务
        Args:
            db: 数据库会话
            task_id: 任务ID
        Returns:
            是否删除成功
        """
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            return False

        # 如果正在下载,先停止
        if task.status == TaskStatus.DOWNLOADING and task_id in self.active_tasks:
            self.downloader.stop_download()
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]

        # 删除文件
        if task.file_path and os.path.exists(task.file_path):
            try:
                os.remove(task.file_path)
            except Exception as e:
                logger.error(f"删除文件失败: {e}")

        # 清理临时文件
        if task.temp_path:
            self.downloader.clean_temp_files(task.temp_path)

        # 删除任务记录
        db.delete(task)
        db.commit()

        return True

    async def retry_task(self, db: Session, task_id: str, cookies: Optional[str] = None):
        """
        重试失败的任务
        Args:
            db: 数据库会话
            task_id: 任务ID
            cookies: Cookie字符串
        """
        task = db.query(DownloadTask).filter(DownloadTask.task_id == task_id).first()
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        if task.status != TaskStatus.FAILED:
            raise ValueError(f"任务未失败,无法重试: {task_id}")

        # 重置任务状态
        task.status = TaskStatus.PENDING
        task.error_message = None
        db.commit()

        # 重新开始下载
        await self.start_task(db, task_id, cookies)


# 全局任务管理器实例
task_manager = TaskManager()
