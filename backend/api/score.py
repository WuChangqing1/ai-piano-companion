"""曲谱上传接口。"""
from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_models.omr_parser import parse_score
from db.database import get_db
from db import models

router = APIRouter(prefix="/api", tags=["score"])

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "scores"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload_score")
async def upload_score(
    file: UploadFile = File(...),
    title: str = "未命名曲目",
    db: Session = Depends(get_db),
):
    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in {"jpg", "jpeg", "png", "pdf"}:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/pdf")

    save_path = _UPLOAD_DIR / f"{uuid.uuid4().hex}.{ext}"
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(await file.read())

    parsed = parse_score(save_path)
    score = models.Score(
        score_uid=parsed["score_uid"],
        title=title,
        midi_path=parsed["midi_path"],
        measure_count=parsed["measure_count"],
    )
    db.add(score)
    db.commit()
    db.refresh(score)

    midi_url = f"/static/{Path(parsed['midi_path']).name}"
    return {
        "status": "success",
        "score_id": parsed["score_uid"],
        "midi_url": midi_url,
        "measure_count": parsed["measure_count"],
    }
