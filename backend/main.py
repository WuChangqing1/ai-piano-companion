"""
AI 琴伴 - FastAPI 入口
启动:  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

# 确保子模块以绝对路径方式导入
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests

from api import score, evaluate, config as config_api, reports, auth
from db.database import init_db

app = FastAPI(
    title="AI琴伴 - Backend",
    description="多模态钢琴陪练后端。允许用户在 App 内自定义模型 API。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
_ICONS_DIR = _STATIC_DIR / "icons"
_ICONS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
app.mount("/icons", StaticFiles(directory=str(_ICONS_DIR)), name="icons")

app.include_router(auth.router)
app.include_router(config_api.router)
app.include_router(score.router)
app.include_router(evaluate.router)
app.include_router(reports.router)


@app.on_event("startup")
async def on_startup():
    init_db()


@app.get("/")
async def root():
    """默认首页 → demo.html"""
    demo_path = _STATIC_DIR / "demo.html"
    if demo_path.exists():
        return FileResponse(demo_path)
    return {
        "service": "AI琴伴 backend",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/demo")
async def demo():
    """PC 浏览器演示页面"""
    demo_path = _STATIC_DIR / "demo.html"
    if demo_path.exists():
        return FileResponse(demo_path)
    return {"error": "demo.html not found"}


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/api/cosyvoice/speakers")
async def cosyvoice_speakers():
    """代理 CosyVoice 音色列表，解决手机无法直接访问 127.0.0.1:9880 的问题"""
    try:
        resp = requests.get("http://127.0.0.1:9880/speakers", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # 返回默认列表
    return {"speakers": ["中文女", "中文男", "英文女", "英文男"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
