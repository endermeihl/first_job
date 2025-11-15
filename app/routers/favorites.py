"""
收藏夹路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..schemas import Favorite, FavoriteCreate, FavoriteVideo, FavoriteVideoCreate
from ..models import Favorite as FavoriteModel, FavoriteVideo as FavoriteVideoModel
from ..services.xiaohongshu_api import XiaohongshuAPI
from ..services.task_manager import task_manager
from ..schemas import DownloadTaskCreate, VideoQuality

router = APIRouter(prefix="/api/favorites", tags=["收藏夹管理"])


@router.post("/", response_model=Favorite)
async def create_favorite(favorite_data: FavoriteCreate, db: Session = Depends(get_db)):
    """
    创建收藏夹
    """
    # 检查是否已存在
    existing = db.query(FavoriteModel).filter(
        FavoriteModel.favorite_id == favorite_data.favorite_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="收藏夹已存在")

    favorite = FavoriteModel(**favorite_data.dict())
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


@router.get("/", response_model=List[Favorite])
async def get_favorites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取收藏夹列表
    """
    favorites = db.query(FavoriteModel).offset(skip).limit(limit).all()
    return favorites


@router.get("/{favorite_id}", response_model=Favorite)
async def get_favorite(favorite_id: str, db: Session = Depends(get_db)):
    """
    获取收藏夹详情
    """
    favorite = db.query(FavoriteModel).filter(
        FavoriteModel.favorite_id == favorite_id
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="收藏夹不存在")

    return favorite


@router.post("/{favorite_id}/sync")
async def sync_favorite(
    favorite_id: str,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    同步收藏夹(从小红书获取最新视频列表)
    """
    try:
        favorite = db.query(FavoriteModel).filter(
            FavoriteModel.favorite_id == favorite_id
        ).first()

        if not favorite:
            raise HTTPException(status_code=404, detail="收藏夹不存在")

        # 获取收藏夹视频
        xhs_api = XiaohongshuAPI(cookies)
        videos_data = await xhs_api.get_favorite_videos(favorite_id)

        video_list = videos_data.get('list', [])
        synced_count = 0

        for video in video_list:
            video_id = video.get('note_id') or video.get('id')
            if not video_id:
                continue

            # 检查是否已存在
            existing = db.query(FavoriteVideoModel).filter(
                FavoriteVideoModel.favorite_id == favorite_id,
                FavoriteVideoModel.video_id == video_id
            ).first()

            if not existing:
                # 添加新视频
                new_video = FavoriteVideoModel(
                    favorite_id=favorite_id,
                    video_id=video_id,
                    video_url=f"https://www.xiaohongshu.com/explore/{video_id}",
                    title=video.get('title') or video.get('display_title', ''),
                    author=video.get('user', {}).get('nickname', ''),
                    cover_url=video.get('cover', {}).get('url', ''),
                    is_valid=1,
                    is_downloaded=0
                )
                db.add(new_video)
                synced_count += 1

        # 更新收藏夹信息
        favorite.video_count = db.query(FavoriteVideoModel).filter(
            FavoriteVideoModel.favorite_id == favorite_id
        ).count()
        favorite.last_sync_at = datetime.now()

        db.commit()

        return {
            "code": 200,
            "message": f"同步成功,新增 {synced_count} 个视频",
            "data": {
                "favorite_id": favorite_id,
                "synced_count": synced_count,
                "total_count": favorite.video_count
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{favorite_id}/videos", response_model=List[FavoriteVideo])
async def get_favorite_videos(
    favorite_id: str,
    valid_only: bool = Query(True, description="仅显示有效视频"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取收藏夹中的视频列表
    """
    query = db.query(FavoriteVideoModel).filter(
        FavoriteVideoModel.favorite_id == favorite_id
    )

    if valid_only:
        query = query.filter(FavoriteVideoModel.is_valid == 1)

    videos = query.offset(skip).limit(limit).all()
    return videos


@router.post("/{favorite_id}/check-invalid")
async def check_invalid_videos(
    favorite_id: str,
    background_tasks: BackgroundTasks,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    检测收藏夹中的失效视频
    """
    async def check_task():
        xhs_api = XiaohongshuAPI(cookies)
        videos = db.query(FavoriteVideoModel).filter(
            FavoriteVideoModel.favorite_id == favorite_id
        ).all()

        invalid_count = 0
        for video in videos:
            is_valid = await xhs_api.check_video_valid(video.video_id)
            if not is_valid:
                video.is_valid = 0
                invalid_count += 1

        # 更新收藏夹失效计数
        favorite = db.query(FavoriteModel).filter(
            FavoriteModel.favorite_id == favorite_id
        ).first()
        if favorite:
            favorite.invalid_count = invalid_count

        db.commit()

    background_tasks.add_task(check_task)

    return {
        "code": 200,
        "message": "检测任务已启动",
        "data": {"favorite_id": favorite_id}
    }


@router.post("/{favorite_id}/download-all")
async def download_all_videos(
    favorite_id: str,
    quality: VideoQuality = VideoQuality.HD,
    valid_only: bool = True,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    批量下载收藏夹中的所有视频
    """
    try:
        query = db.query(FavoriteVideoModel).filter(
            FavoriteVideoModel.favorite_id == favorite_id,
            FavoriteVideoModel.is_downloaded == 0
        )

        if valid_only:
            query = query.filter(FavoriteVideoModel.is_valid == 1)

        videos = query.all()

        if not videos:
            return {
                "code": 200,
                "message": "没有需要下载的视频",
                "data": {"count": 0}
            }

        # 为每个视频创建下载任务
        created_tasks = []
        for video in videos:
            task_data = DownloadTaskCreate(
                video_url=video.video_url,
                quality=quality,
                parts=None
            )
            task = await task_manager.create_task(db, task_data, cookies)
            created_tasks.append(task.task_id)

        return {
            "code": 200,
            "message": f"已创建 {len(created_tasks)} 个下载任务",
            "data": {
                "favorite_id": favorite_id,
                "task_count": len(created_tasks),
                "task_ids": created_tasks
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{favorite_id}")
async def delete_favorite(favorite_id: str, db: Session = Depends(get_db)):
    """
    删除收藏夹
    """
    favorite = db.query(FavoriteModel).filter(
        FavoriteModel.favorite_id == favorite_id
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="收藏夹不存在")

    # 删除收藏夹中的所有视频
    db.query(FavoriteVideoModel).filter(
        FavoriteVideoModel.favorite_id == favorite_id
    ).delete()

    # 删除收藏夹
    db.delete(favorite)
    db.commit()

    return {
        "code": 200,
        "message": "收藏夹已删除",
        "data": {"favorite_id": favorite_id}
    }
