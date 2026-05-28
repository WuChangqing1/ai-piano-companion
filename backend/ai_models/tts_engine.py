"""
TTS 引擎封装。
CosyVoice HTTP API（优先）+ edge-tts 兜底。
CosyVoice API 文档: docs/cosyvoice使用手册.md
"""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import edge_tts
import requests

from core.config_manager import get_config

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)


async def synthesize(text: str) -> Path:
    """把文本合成为音频,返回静态目录下的文件路径。"""
    cfg = get_config()["tts"]
    engine = cfg.get("engine", "edge-tts")

    if engine == "cosyvoice":
        return await asyncio.to_thread(_synthesize_cosyvoice, text, cfg)
    return await _synthesize_edge(text, cfg)


async def _synthesize_edge(text: str, cfg: dict) -> Path:
    voice = cfg.get("voice", "zh-CN-XiaoxiaoNeural")
    rate = cfg.get("rate", "+0%")
    pitch = cfg.get("pitch", "+0Hz")
    out = _STATIC_DIR / f"tts_{uuid.uuid4().hex}.mp3"
    tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await tts.save(str(out))
    return out


def _synthesize_cosyvoice(text: str, cfg: dict) -> Path:
    """调用 CosyVoice HTTP API 合成语音。失败时回退 edge-tts。"""
    api_url = cfg.get("cosyvoice_url", "http://127.0.0.1:9880")
    speaker = cfg.get("cosyvoice_speaker", "中文女")
    speed = cfg.get("cosyvoice_speed", 1.0)

    out = _STATIC_DIR / f"tts_{uuid.uuid4().hex}.wav"

    try:
        resp = requests.get(
            f"{api_url}/",
            params={"text": text, "speaker": speaker, "speed": speed},
            timeout=120,
        )
        if resp.status_code == 200 and len(resp.content) > 0:
            out.write_bytes(resp.content)
            return out
    except Exception:
        pass

    # 回退到 edge-tts
    return _synthesize_edge_sync(text)


def _synthesize_edge_sync(text: str) -> Path:
    """edge-tts 同步兜底。"""
    out = _STATIC_DIR / f"tts_{uuid.uuid4().hex}.mp3"
    try:
        asyncio.run(
            edge_tts.Communicate(
                text=text, voice="zh-CN-XiaoxiaoNeural"
            ).save(str(out))
        )
    except Exception:
        pass
    return out


def synthesize_sync(text: str, output_dir: Path = None) -> Path | None:
    """同步版 TTS（用于测试流水线等非 async 场景）。

    优先 CosyVoice HTTP API，失败回退 edge-tts。

    Args:
        text: 要合成的文本
        output_dir: 输出目录，默认使用 _STATIC_DIR

    Returns: 音频文件路径，失败返回 None
    """
    cfg = get_config()["tts"]
    engine = cfg.get("engine", "edge-tts")
    save_dir = output_dir or _STATIC_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    if engine == "cosyvoice":
        api_url = cfg.get("cosyvoice_url", "http://127.0.0.1:9880")
        speaker = cfg.get("cosyvoice_speaker", "中文女")
        speed = cfg.get("cosyvoice_speed", 1.0)
        out = save_dir / f"tts_{uuid.uuid4().hex}.wav"

        try:
            resp = requests.get(
                f"{api_url}/",
                params={"text": text, "speaker": speaker, "speed": speed},
                timeout=120,
            )
            if resp.status_code == 200 and len(resp.content) > 0:
                out.write_bytes(resp.content)
                return out
        except Exception:
            pass

    # edge-tts 兜底
    out = save_dir / f"tts_{uuid.uuid4().hex}.mp3"
    try:
        asyncio.run(
            edge_tts.Communicate(
                text=text, voice="zh-CN-XiaoxiaoNeural"
            ).save(str(out))
        )
        return out
    except Exception:
        return None
