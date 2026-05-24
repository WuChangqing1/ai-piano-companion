"""
TTS 引擎封装。
默认 edge-tts(免费、无 key、中文情感语音),
可在配置里切换 voice。CosyVoice 接入位置已留好。
"""
from __future__ import annotations

import uuid
from pathlib import Path

import edge_tts

from core.config_manager import get_config

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)


async def synthesize(text: str) -> Path:
    """把文本合成为 wav,返回静态目录下的文件路径。"""
    cfg = get_config()["tts"]
    engine = cfg.get("engine", "edge-tts")

    if engine == "cosyvoice":
        return await _synthesize_cosyvoice(text, cfg)
    return await _synthesize_edge(text, cfg)


async def _synthesize_edge(text: str, cfg: dict) -> Path:
    voice = cfg.get("voice", "zh-CN-XiaoxiaoNeural")
    rate = cfg.get("rate", "+0%")
    pitch = cfg.get("pitch", "+0Hz")
    out = _STATIC_DIR / f"tts_{uuid.uuid4().hex}.mp3"
    tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await tts.save(str(out))
    return out


async def _synthesize_cosyvoice(text: str, cfg: dict) -> Path:
    """CosyVoice 占位 - 接入真实模型时在此实现。"""
    # 占位:落回 edge-tts 保障可用
    return await _synthesize_edge(text, cfg)
