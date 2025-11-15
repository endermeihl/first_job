"""
配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "小红书视频下载工具"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./xiaohongshu_downloader.db"

    # 下载配置
    DOWNLOAD_DIR: str = "./downloads"
    MAX_CONCURRENT_DOWNLOADS: int = 3
    CHUNK_SIZE: int = 1024 * 1024  # 1MB
    RETRY_TIMES: int = 3
    TIMEOUT: int = 30

    # 小红书API配置
    XHS_BASE_URL: str = "https://www.xiaohongshu.com"
    XHS_API_BASE_URL: str = "https://edith.xiaohongshu.com"

    # Cookie存储路径
    COOKIE_FILE: str = "./cookies.json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# 确保下载目录存在
os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
