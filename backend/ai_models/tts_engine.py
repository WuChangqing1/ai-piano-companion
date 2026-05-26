"""
TTS 引擎封装。
默认 edge-tts(免费、无需 key、中文情感语音);
CosyVoice 通过独立子进程调用,需单独配置环境。
"""
from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

import edge_tts

from core.config_manager import get_config

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)

# CosyVoice 桥接脚本路径
_COSYVOICE_SCRIPT = Path(__file__).resolve().parent / "cosyvoice_bridge.py"


async def synthesize(text: str) -> Path:
    """把文本合成为音频,返回静态目录下的文件路径。"""
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
    """
    CosyVoice 调用:通过独立 Python 脚本 + conda 环境运行。
    需要先配置 CosyVoice 环境,见 docs/ 目录。
    失败时自动回退到 edge-tts。
    """
    out = _STATIC_DIR / f"tts_{uuid.uuid4().hex}.wav"

    # 查找包含 CosyVoice 的 conda 环境
    cosyvoice_env = cfg.get("cosyvoice_env", "AIqinban-models")
    ref_audio = cfg.get("ref_audio", None)  # Zero-shot 参考音频路径
    ref_text = cfg.get("ref_text", "宝贝弹得很完整,老师能感觉到你认真练习了")
    voice = cfg.get("cosyvoice_voice", "中文女")

    cmd = [
        "conda", "run", "-n", cosyvoice_env, "python",
        str(_COSYVOICE_SCRIPT),
        "--text", text,
        "--output", str(out),
        "--voice", voice,
    ]
    if ref_audio:
        cmd += ["--ref-audio", ref_audio, "--ref-text", ref_text]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return out
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 回退到 edge-tts
    mp3_out = out.with_suffix(".mp3")
    tts = edge_tts.Communicate(text=text, voice="zh-CN-XiaoxiaoNeural")
    await tts.save(str(mp3_out))
    return mp3_out
