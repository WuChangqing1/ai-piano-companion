"""
ByteDance Piano Transcription 封装。
MVP 阶段返回 Mock 数据,跑通后再接真实模型。
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

NOTE_NAMES = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]


def transcribe_and_diff(video_path: Path, standard_midi: Path | None = None) -> dict[str, Any]:
    """
    输入练习视频(自动剥离音频)与标准 MIDI,
    输出 diff 结果:错音、漏音、多余音 + 节奏稳定性评分。
    """
    wrong = []
    missing = []
    extra = []
    for _ in range(random.randint(0, 3)):
        ts = round(random.uniform(2.0, 60.0), 2)
        wrong.append({
            "timestamp": ts,
            "measure": max(1, int(ts // 2)),
            "issue_type": "wrong_note",
            "expected": random.choice(NOTE_NAMES),
            "actual": random.choice(NOTE_NAMES),
        })
    for _ in range(random.randint(0, 2)):
        ts = round(random.uniform(2.0, 60.0), 2)
        missing.append({
            "timestamp": ts,
            "measure": max(1, int(ts // 2)),
            "issue_type": "missing_note",
            "expected": random.choice(NOTE_NAMES),
            "actual": None,
        })

    return {
        "wrong": wrong,
        "missing": missing,
        "extra": extra,
        "rhythm_score": random.randint(75, 95),
        "duration": round(random.uniform(30.0, 90.0), 1),
    }
