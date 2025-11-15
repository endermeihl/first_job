"""
视频下载路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..schemas import VideoInfo
from ..services.xiaohongshu_api import XiaohongshuAPI

router = APIRouter(prefix="/api/videos", tags=["视频信息"])


@router.get("/info")
async def get_video_info(
    url: str = Query(..., description="视频URL"),
    cookies: Optional[str] = Query(None, description="Cookie字符串")
):
    """
    获取视频信息
    """
    try:
        xhs_api = XiaohongshuAPI(cookies)
        video_info = await xhs_api.get_video_info(url)
        return {
            "code": 200,
            "message": "success",
            "data": video_info
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/download-url")
async def get_download_url(
    video_id: str = Query(..., description="视频ID"),
    quality: str = Query("hd", description="视频质量 hd/sd/ld"),
    cookies: Optional[str] = Query(None, description="Cookie字符串")
):
    """
    获取视频下载链接
    """
    try:
        xhs_api = XiaohongshuAPI(cookies)
        download_url = await xhs_api.get_download_url(video_id, quality)

        if not download_url:
            raise HTTPException(status_code=404, detail="无法获取下载链接")

        return {
            "code": 200,
            "message": "success",
            "data": {
                "video_id": video_id,
                "quality": quality,
                "download_url": download_url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check-valid")
async def check_video_valid(
    video_id: str = Query(..., description="视频ID"),
    cookies: Optional[str] = Query(None, description="Cookie字符串")
):
    """
    检查视频是否有效
    """
    try:
        xhs_api = XiaohongshuAPI(cookies)
        is_valid = await xhs_api.check_video_valid(video_id)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "video_id": video_id,
                "is_valid": is_valid
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
