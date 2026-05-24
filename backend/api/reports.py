"""学情报告查询。"""
from __future__ import annotations

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db import models

router = APIRouter(prefix="/api", tags=["reports"])


@router.get("/reports")
async def list_reports(user_id: int | None = None, limit: int = 20,
                       db: Session = Depends(get_db)):
    q = db.query(models.PracticeReport)
    if user_id:
        q = q.filter(models.PracticeReport.user_id == user_id)
    rows = q.order_by(models.PracticeReport.created_at.desc()).limit(limit).all()
    return [{
        "report_id": r.report_uid,
        "created_at": r.created_at.isoformat(),
        "overall_score": r.overall_score,
        "rhythm_score": r.rhythm_score,
        "accuracy_score": r.accuracy_score,
        "hand_health_score": r.hand_health_score,
        "teacher_comment": r.teacher_comment,
    } for r in rows]


@router.get("/reports/{report_id}")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    r = db.query(models.PracticeReport).filter_by(report_uid=report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {
        "report_id": r.report_uid,
        "created_at": r.created_at.isoformat(),
        "report": json.loads(r.raw_json),
    }
