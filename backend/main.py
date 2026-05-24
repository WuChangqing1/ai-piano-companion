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

from api import score, evaluate, config as config_api, reports, auth
from db.database import init_db

app = FastAPI(
    title="AI 琴伴 - Backend",
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
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

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
    return {
        "service": "AI 琴伴 backend",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
