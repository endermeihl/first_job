from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base
import enum


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class VideoQuality(str, enum.Enum):
    """视频质量枚举"""
    HD = "hd"  # 高清
    SD = "sd"  # 标清
    LD = "ld"  # 流畅


class DownloadTask(Base):
    """下载任务模型"""
    __tablename__ = "download_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)  # 任务唯一ID
    video_url = Column(String, nullable=False)  # 视频URL
    video_id = Column(String, index=True)  # 小红书视频ID
    title = Column(String)  # 视频标题
    author = Column(String)  # 作者
    cover_url = Column(String)  # 封面URL

    # 下载配置
    quality = Column(SQLEnum(VideoQuality), default=VideoQuality.HD)  # 视频质量
    parts = Column(JSON)  # 选择下载的分P列表 [1,2,3] 或 null表示全部

    # 任务状态
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    progress = Column(Float, default=0.0)  # 下载进度 0-100
    downloaded_size = Column(Integer, default=0)  # 已下载大小(字节)
    total_size = Column(Integer, default=0)  # 总大小(字节)
    speed = Column(Float, default=0.0)  # 下载速度(KB/s)

    # 文件信息
    file_path = Column(String)  # 保存路径
    temp_path = Column(String)  # 临时文件路径(用于断点续传)

    # 错误信息
    error_message = Column(Text)  # 错误信息
    retry_count = Column(Integer, default=0)  # 重试次数

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime)  # 开始下载时间
    completed_at = Column(DateTime)  # 完成时间


class Favorite(Base):
    """收藏夹模型"""
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    favorite_id = Column(String, unique=True, index=True, nullable=False)  # 收藏夹ID
    name = Column(String, nullable=False)  # 收藏夹名称
    description = Column(Text)  # 描述
    cover_url = Column(String)  # 封面

    video_count = Column(Integer, default=0)  # 视频数量
    invalid_count = Column(Integer, default=0)  # 失效视频数量

    last_sync_at = Column(DateTime)  # 最后同步时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FavoriteVideo(Base):
    """收藏夹视频模型"""
    __tablename__ = "favorite_videos"

    id = Column(Integer, primary_key=True, index=True)
    favorite_id = Column(String, index=True, nullable=False)  # 所属收藏夹ID
    video_id = Column(String, index=True, nullable=False)  # 视频ID
    video_url = Column(String, nullable=False)  # 视频URL
    title = Column(String)  # 标题
    author = Column(String)  # 作者
    cover_url = Column(String)  # 封面

    is_valid = Column(Integer, default=1)  # 是否有效 1-有效 0-失效
    is_downloaded = Column(Integer, default=0)  # 是否已下载

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserAuth(Base):
    """用户认证信息模型"""
    __tablename__ = "user_auth"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)  # 用户ID
    username = Column(String)  # 用户名
    cookies = Column(Text, nullable=False)  # Cookie JSON字符串

    is_valid = Column(Integer, default=1)  # Cookie是否有效
    last_validated_at = Column(DateTime)  # 最后验证时间

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Item(Base):
    """示例Item模型(可删除)"""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
