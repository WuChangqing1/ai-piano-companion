"""
运行时配置管理:读 / 写 config.json,支持热更新。
线程安全的原子写入,前端改了配置后,下一次 LLM/TTS 调用立即生效。
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
_CACHE: dict[str, Any] | None = None


def _load_from_disk() -> dict[str, Any]:
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_config() -> dict[str, Any]:
    """返回当前内存中的配置(只读副本)。"""
    global _CACHE
    with _LOCK:
        if _CACHE is None:
            _CACHE = _load_from_disk()
        return json.loads(json.dumps(_CACHE))


def update_config(patch: dict[str, Any]) -> dict[str, Any]:
    """
    深度合并 patch 到当前配置,原子写回磁盘,刷新内存缓存。
    返回更新后的完整配置。
    """
    global _CACHE
    with _LOCK:
        current = _load_from_disk()
        merged = _deep_merge(current, patch)
        tmp_path = _CONFIG_PATH.with_suffix(".json.tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, _CONFIG_PATH)
        _CACHE = merged
        return json.loads(json.dumps(merged))


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def mask_secrets(cfg: dict[str, Any]) -> dict[str, Any]:
    """对外暴露时把 api_key 掩码,只显示后 4 位。"""
    out = json.loads(json.dumps(cfg))
    key = out.get("llm", {}).get("api_key", "") or ""
    if key:
        out["llm"]["api_key"] = "****" + key[-4:] if len(key) > 4 else "****"
    return out
