"""
用户认证路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import UserAuth, UserAuthCreate
from ..models import UserAuth as UserAuthModel
from ..services.xiaohongshu_api import XiaohongshuAPI
from datetime import datetime
import json
import hashlib

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


@router.post("/login", response_model=UserAuth)
async def login(auth_data: UserAuthCreate, db: Session = Depends(get_db)):
    """
    使用Cookie登录
    """
    try:
        # 验证Cookie
        xhs_api = XiaohongshuAPI(auth_data.cookies)
        is_valid = await xhs_api.validate_cookies()

        if not is_valid:
            raise HTTPException(status_code=401, detail="Cookie无效")

        # 生成用户ID (基于Cookie的hash)
        user_id = hashlib.md5(auth_data.cookies.encode()).hexdigest()[:16]

        # 查询是否已存在
        existing_auth = db.query(UserAuthModel).filter(
            UserAuthModel.user_id == user_id
        ).first()

        if existing_auth:
            # 更新Cookie
            existing_auth.cookies = auth_data.cookies
            existing_auth.is_valid = 1
            existing_auth.last_validated_at = datetime.now()
            db.commit()
            db.refresh(existing_auth)
            return existing_auth
        else:
            # 创建新记录
            new_auth = UserAuthModel(
                user_id=user_id,
                cookies=auth_data.cookies,
                is_valid=1,
                last_validated_at=datetime.now()
            )
            db.add(new_auth)
            db.commit()
            db.refresh(new_auth)
            return new_auth

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate")
async def validate_cookies(auth_data: UserAuthCreate):
    """
    验证Cookie是否有效
    """
    try:
        xhs_api = XiaohongshuAPI(auth_data.cookies)
        is_valid = await xhs_api.validate_cookies()

        return {
            "code": 200,
            "message": "success",
            "data": {
                "is_valid": is_valid
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/current", response_model=UserAuth)
async def get_current_user(user_id: str, db: Session = Depends(get_db)):
    """
    获取当前用户信息
    """
    user_auth = db.query(UserAuthModel).filter(
        UserAuthModel.user_id == user_id
    ).first()

    if not user_auth:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user_auth


@router.delete("/logout")
async def logout(user_id: str, db: Session = Depends(get_db)):
    """
    登出(删除Cookie)
    """
    user_auth = db.query(UserAuthModel).filter(
        UserAuthModel.user_id == user_id
    ).first()

    if not user_auth:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user_auth)
    db.commit()

    return {
        "code": 200,
        "message": "已登出",
        "data": {"user_id": user_id}
    }
