from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ===== 枚举类型 =====
class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class VideoQuality(str, Enum):
    """视频质量"""
    HD = "hd"
    SD = "sd"
    LD = "ld"


# ===== 下载任务相关 =====
class DownloadTaskCreate(BaseModel):
    """创建下载任务"""
    video_url: str = Field(..., description="视频URL")
    quality: VideoQuality = Field(VideoQuality.HD, description="视频质量")
    parts: Optional[List[int]] = Field(None, description="选择下载的分P,null表示全部")


class DownloadTaskUpdate(BaseModel):
    """更新下载任务"""
    status: Optional[TaskStatus] = None
    progress: Optional[float] = None
    downloaded_size: Optional[int] = None
    total_size: Optional[int] = None
    speed: Optional[float] = None
    error_message: Optional[str] = None


class DownloadTask(BaseModel):
    """下载任务响应"""
    id: int
    task_id: str
    video_url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    cover_url: Optional[str] = None

    quality: VideoQuality
    parts: Optional[List[int]] = None

    status: TaskStatus
    progress: float
    downloaded_size: int
    total_size: int
    speed: float

    file_path: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int

    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== 收藏夹相关 =====
class FavoriteCreate(BaseModel):
    """创建收藏夹"""
    favorite_id: str = Field(..., description="收藏夹ID")
    name: str = Field(..., description="收藏夹名称")
    description: Optional[str] = None
    cover_url: Optional[str] = None


class Favorite(BaseModel):
    """收藏夹响应"""
    id: int
    favorite_id: str
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    video_count: int
    invalid_count: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FavoriteVideoCreate(BaseModel):
    """添加收藏夹视频"""
    favorite_id: str
    video_id: str
    video_url: str
    title: Optional[str] = None
    author: Optional[str] = None
    cover_url: Optional[str] = None


class FavoriteVideo(BaseModel):
    """收藏夹视频响应"""
    id: int
    favorite_id: str
    video_id: str
    video_url: str
    title: Optional[str] = None
    author: Optional[str] = None
    cover_url: Optional[str] = None
    is_valid: int
    is_downloaded: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== 用户认证相关 =====
class UserAuthCreate(BaseModel):
    """创建用户认证"""
    cookies: str = Field(..., description="Cookie JSON字符串")


class UserAuth(BaseModel):
    """用户认证响应"""
    id: int
    user_id: Optional[str] = None
    username: Optional[str] = None
    is_valid: int
    last_validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== 通用响应 =====
class ResponseModel(BaseModel):
    """通用响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="消息")
    data: Optional[dict] = Field(None, description="数据")


class VideoInfo(BaseModel):
    """视频信息"""
    video_id: str
    title: str
    author: str
    cover_url: Optional[str] = None
    duration: Optional[int] = None
    parts: List[dict] = Field(default_factory=list, description="分P信息")
    available_qualities: List[VideoQuality] = Field(default_factory=list, description="可用画质")


# ===== 示例Item (可删除) =====
class ItemBase(BaseModel):
    name: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int

    class Config:
        from_attributes = True
