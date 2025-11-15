"""
任务管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas import DownloadTask, DownloadTaskCreate, ResponseModel, TaskStatus
from ..services.task_manager import task_manager

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


@router.post("/", response_model=DownloadTask)
async def create_task(
    task_data: DownloadTaskCreate,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    创建下载任务
    """
    try:
        task = await task_manager.create_task(db, task_data, cookies)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/start")
async def start_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    启动下载任务
    """
    try:
        background_tasks.add_task(task_manager.start_task, db, task_id, cookies)
        return {"code": 200, "message": "任务已启动", "data": {"task_id": task_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/stop")
async def stop_task(task_id: str, db: Session = Depends(get_db)):
    """
    停止下载任务
    """
    try:
        await task_manager.stop_task(db, task_id)
        return {"code": 200, "message": "任务已停止", "data": {"task_id": task_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/pause")
async def pause_task(task_id: str, db: Session = Depends(get_db)):
    """
    暂停下载任务
    """
    try:
        await task_manager.pause_task(db, task_id)
        return {"code": 200, "message": "任务已暂停", "data": {"task_id": task_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    恢复下载任务
    """
    try:
        background_tasks.add_task(task_manager.resume_task, db, task_id, cookies)
        return {"code": 200, "message": "任务已恢复", "data": {"task_id": task_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    cookies: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    重试失败的任务
    """
    try:
        background_tasks.add_task(task_manager.retry_task, db, task_id, cookies)
        return {"code": 200, "message": "任务已重试", "data": {"task_id": task_id}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}", response_model=DownloadTask)
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """
    获取任务详情
    """
    task = task_manager.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/", response_model=List[DownloadTask])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    """
    tasks = task_manager.get_tasks(db, status, skip, limit)
    return tasks


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """
    删除任务
    """
    success = task_manager.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"code": 200, "message": "任务已删除", "data": {"task_id": task_id}}
