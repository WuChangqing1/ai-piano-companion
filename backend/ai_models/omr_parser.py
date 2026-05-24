"""
Oemer OMR 引擎封装。MVP 用 Mock,接口形态对齐真实输出。
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)


def parse_score(score_file: Path) -> dict[str, Any]:
    """把曲谱图片/PDF 解析成标准 MIDI(此处用 Mock 文件占位)。"""
    score_uid = uuid.uuid4().hex
    target = _STATIC_DIR / f"score_{score_uid}.mid"
    # 占位:写一个空文件,真实接入时替换为 Oemer 输出
    target.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")
    return {
        "score_uid": score_uid,
        "midi_path": str(target),
        "measure_count": 24,  # mock
    }
