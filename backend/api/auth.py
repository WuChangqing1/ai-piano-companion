"""极简登录占位:MVP 阶段不做真正的鉴权,只创建/查询用户。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db import models

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginReq(BaseModel):
    phone: str | None = None
    open_id: str | None = None
    nickname: str = "琴童"
    role: str = "child"


@router.post("/login")
async def login(req: LoginReq, db: Session = Depends(get_db)):
    user: models.User | None = None
    if req.phone:
        user = db.query(models.User).filter_by(phone=req.phone).first()
    elif req.open_id:
        user = db.query(models.User).filter_by(open_id=req.open_id).first()
    if not user:
        user = models.User(phone=req.phone, open_id=req.open_id,
                           nickname=req.nickname, role=req.role)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {
        "user_id": user.id,
        "nickname": user.nickname,
        "role": user.role,
    }
