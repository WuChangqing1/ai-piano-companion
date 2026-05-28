"""评估接口 - 整条多模态评估链路入口。"""
from __future__ import annotations

import json
import random
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ai_models.hand_tracker import analyze_hands
from ai_models.audio_amt import transcribe_and_diff
from ai_models.llm_client import generate_teacher_comment
from ai_models.tts_engine import synthesize
from db.database import get_db
from db import models

router = APIRouter(prefix="/api", tags=["evaluate"])

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads" / "videos"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _compose_scores(audio_diff: dict, hand_data: dict) -> dict:
    wrong = len(audio_diff["wrong"])
    missing = len(audio_diff["missing"])

    accuracy = max(40, 100 - wrong * 8 - missing * 6)
    fluency = max(50, 100 - (wrong + missing) * 5)
    hand_health = hand_data.get("hand_score", max(50, 100 - len(hand_data.get("hand_issues", [])) * 12))
    rhythm = audio_diff["rhythm_score"]
    overall = round((accuracy + fluency + hand_health + rhythm) / 4)
    return {
        "overall_score": overall,
        "rhythm_score": rhythm,
        "accuracy_score": accuracy,
        "fluency_score": fluency,
        "hand_health_score": hand_health,
    }


@router.post("/evaluate")
async def evaluate(
    request: Request,
    file: UploadFile = File(...),
    score_id: str | None = Form(None),
    user_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    if not (file.filename or "").lower().endswith((".mp4", ".mov", ".m4v")):
        raise HTTPException(status_code=400, detail="仅支持 mp4/mov 视频")

    video_path = _UPLOAD_DIR / f"{uuid.uuid4().hex}.mp4"
    async with aiofiles.open(video_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)

    # 1. 视觉 — 完整手型分析（含骨架标注 + base64 图片）
    hand_data = analyze_hands(video_path)
    hand_issues = hand_data.get("hand_issues", [])
    # 2. 音频
    audio_diff = transcribe_and_diff(video_path, None)
    # 3. LLM 评语
    comment = await generate_teacher_comment({
        "wrong": audio_diff["wrong"],
        "missing": audio_diff["missing"],
        "hands": hand_issues,
    })
    # 4. TTS
    audio_file = await synthesize(comment)

    scores = _compose_scores(audio_diff, hand_data)
    report_uid = uuid.uuid4().hex

    report_payload = {
        **scores,
        "wrong_notes": len(audio_diff["wrong"]),
        "missing_notes": len(audio_diff["missing"]),
        "hand_issues_count": len(hand_issues),
        "teacher_comment": comment,
        "hand_issues": hand_issues,
        "audio_issues": audio_diff["wrong"] + audio_diff["missing"],
        "duration_seconds": audio_diff["duration"],
        # 手型完整分析数据（含图片）
        "hand_score": hand_data["hand_score"],
        "worst_frames": hand_data["worst_frames"],
        "issues_by_type": hand_data.get("issues_by_type", {}),
        "issues_by_finger": hand_data.get("issues_by_finger", {}),
        "issue_type_names": hand_data.get("issue_type_names", {}),
        "total_frames_sampled": hand_data["total_frames_sampled"],
        "frames_with_hands": hand_data["frames_with_hands"],
    }

    # 持久化
    db_report = models.PracticeReport(
        report_uid=report_uid,
        user_id=user_id,
        score_id=None,
        teacher_comment=comment,
        raw_json=json.dumps(report_payload, ensure_ascii=False),
        audio_path=str(audio_file),
        **scores,
        wrong_notes=len(audio_diff["wrong"]),
        missing_notes=len(audio_diff["missing"]),
        hand_issues_count=len(hand_issues),
        duration_seconds=audio_diff["duration"],
    )
    db.add(db_report)
    db.commit()

    base_url = str(request.base_url).rstrip("/")
    return {
        "status": "success",
        "report_id": report_uid,
        "report": report_payload,
        "audio_url": f"{base_url}/static/{audio_file.name}",
    }
