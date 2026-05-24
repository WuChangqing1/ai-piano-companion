"""
LLM 客户端 - OpenAI 兼容协议。
适配:DeepSeek / 通义 / Moonshot / 智谱 / 本地 Ollama 等所有兼容 OpenAI 的服务。
配置完全来自 core.config_manager,前端改了立即生效。
若 api_key 为空,自动降级到模板话术,保证整链路始终能跑通。
"""
from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI

from core.config_manager import get_config


def _build_user_prompt(template: str, errors: dict[str, Any]) -> str:
    wrong = errors.get("wrong", [])
    missing = errors.get("missing", [])
    hands = errors.get("hands", [])
    wrong_desc = ",".join(
        f"第{e['measure']}小节{e.get('expected','?')}弹成了{e.get('actual','?')}"
        for e in wrong
    ) or "无"
    missing_desc = ",".join(
        f"第{e['measure']}小节漏弹{e.get('expected','?')}"
        for e in missing
    ) or "无"
    hand_desc = ",".join(
        f"第{h['measure']}小节{h['description']}"
        for h in hands
    ) or "无"
    return template.format(
        wrong_notes=wrong_desc,
        missing_notes=missing_desc,
        hand_issues=hand_desc,
    )


def _fallback_comment(errors: dict[str, Any]) -> str:
    n = len(errors.get("wrong", [])) + len(errors.get("missing", []))
    h = len(errors.get("hands", []))
    if n == 0 and h == 0:
        return "宝贝今天弹得非常棒!音准和手型都很标准,继续保持哦~"
    parts = ["宝贝弹得很完整,老师能感觉到你认真练习了！"]
    if n > 0:
        parts.append(f"有 {n} 个小地方音符还可以再准一些")
    if h > 0:
        parts.append(f"还有 {h} 处手型要注意,记得让手指像小桥一样撑起来呀~")
    return "".join(parts)


async def generate_teacher_comment(errors: dict[str, Any]) -> str:
    cfg = get_config()
    llm = cfg["llm"]
    prompt = cfg["prompt"]

    if not llm.get("api_key"):
        return _fallback_comment(errors)

    client = AsyncOpenAI(
        api_key=llm["api_key"],
        base_url=llm["base_url"],
    )
    user_prompt = _build_user_prompt(prompt["user_template"], errors)

    try:
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=llm["model"],
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=float(llm.get("temperature", 0.8)),
                max_tokens=int(llm.get("max_tokens", 200)),
            ),
            timeout=30,
        )
        text = resp.choices[0].message.content or ""
        return text.strip() or _fallback_comment(errors)
    except Exception:
        # 任何异常都回退到模板,保障可用性
        return _fallback_comment(errors)


async def test_connection() -> dict[str, Any]:
    """供 /api/config/test 接口调用,验证用户配的 key 是否可用。"""
    cfg = get_config()["llm"]
    if not cfg.get("api_key"):
        return {"ok": False, "error": "未配置 api_key"}
    client = AsyncOpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    try:
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=8,
            ),
            timeout=15,
        )
        return {"ok": True, "sample": resp.choices[0].message.content}
    except Exception as e:
        return {"ok": False, "error": str(e)}
