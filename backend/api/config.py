"""配置接口 - 前端「设置页」对应,允许用户自定义模型 API。"""
from __future__ import annotations

import requests
from fastapi import APIRouter, HTTPException

from core.config_manager import get_config, update_config, mask_secrets
from core.schemas import ConfigPatch
from ai_models import llm_client

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
async def read_config(reveal: bool = False):
    """
    返回当前配置。
    默认对 api_key 做掩码,reveal=true 时返回明文(仅本地局域网使用)。
    """
    cfg = get_config()
    return cfg if reveal else mask_secrets(cfg)


@router.post("")
async def write_config(patch: ConfigPatch):
    """前端只传想改的字段。空字符串的 api_key 会被忽略,避免误清。"""
    patch_dict = patch.model_dump(exclude_none=True)
    # 防御:如果 api_key 传空串,认为是不改
    if "llm" in patch_dict and patch_dict["llm"].get("api_key") == "":
        patch_dict["llm"].pop("api_key")
    if not patch_dict:
        raise HTTPException(status_code=400, detail="未提供任何变更字段")
    new_cfg = update_config(patch_dict)
    return {"ok": True, "config": mask_secrets(new_cfg)}


@router.post("/test")
async def test_llm():
    """用当前保存的 LLM 配置发一条简单请求,检验可用性。"""
    return await llm_client.test_connection()
