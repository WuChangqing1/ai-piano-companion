# 项目架构

> 最后更新：2026-05-26

## 系统概览

AI 琴伴是一个多模态（视觉+音频）钢琴陪练系统 MVP。用户通过 Flutter App 上传曲谱、录制弹奏视频，后端 FastAPI 服务对手型（MediaPipe）和音频（AMT）进行多模态分析，再经可配置的 LLM 生成温和评语、TTS 合成语音，最终以 2D 数字人形式呈现反馈。

**核心亮点**：用户可在 App 设置页自定义 LLM API（支持 DeepSeek / 通义 / 智谱 / Kimi / 本地 Ollama 等所有 OpenAI 兼容服务）与 TTS 引擎。

## 技术栈

| 层级 | 技术 | 用途 |
|---|---|---|
| 前端 | Flutter 3.19+ / Dart | 移动端 App（摄像头录制、UI、数字人） |
| 后端 | Python 3.11 / FastAPI（Conda 环境 `AIqinban`） | REST API 服务 |
| 数据库 | SQLite 3 + SQLAlchemy 2.x | 本地持久化（用户、曲谱、报告） |
| AI - 手型 | MediaPipe Hands（真实模型 / Mock 兜底） | 21 点手部关键点检测 |
| AI - 音频 | Spotify basic-pitch（ONNX 后端 / Mock 兜底） | 音频转 MIDI |
| AI - 曲谱 | Oemer OMR（ONNX 后端 / Mock 兜底） | 光学乐谱识别 |
| AI - 评语 | OpenAI 兼容 LLM API | 生成温和评语 |
| AI - 语音 | edge-tts / CosyVoice | TTS 合成 |
| 部署 | 局域网部署（uvicorn） | 手机 + PC 同一 Wi-Fi |

## 目录结构

```
ai_qinban_project/
├── backend/                    # Python FastAPI 后端
│   ├── main.py                 # 应用入口
│   ├── config.json             # LLM/TTS 运行时配置（不入 git）
│   ├── requirements.txt        # Python 依赖
│   ├── core/                   # 核心配置与数据模型
│   │   ├── config_manager.py   # 配置管理器（原子读写 config.json）
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── db/                     # 数据库层
│   │   ├── database.py         # SQLAlchemy 引擎与会话管理
│   │   └── models.py           # ORM 模型（users, scores, practice_reports）
│   ├── ai_models/              # AI 模型模块
│   │   ├── hand_tracker.py     # 手型检测（MediaPipe / Mock）
│   │   ├── audio_amt.py        # 音频转录（basic-pitch ONNX / Mock）
│   │   ├── omr_parser.py       # 曲谱识别（Oemer CLI + MusicXML→MIDI / Mock）
│   │   ├── llm_client.py       # LLM 调用（OpenAI 兼容协议）
│   │   └── tts_engine.py       # TTS 合成（edge-tts / CosyVoice）
│   └── api/                    # API 路由
│       ├── config.py           # 配置中心 API
│       ├── score.py            # 曲谱上传 API
│       ├── evaluate.py         # 多模态评估 API（核心）
│       ├── reports.py          # 历史报告 API
│       └── auth.py             # 用户登录 API（占位）
├── frontend_app/               # Flutter 前端
│   ├── lib/
│   │   ├── main.dart           # App 入口
│   │   ├── app_config.dart     # 全局配置
│   │   ├── models/             # 数据模型
│   │   ├── services/           # API 客户端
│   │   ├── widgets/            # 组件（avatar_2d 数字人）
│   │   └── screens/            # 页面（home, practice, feedback, settings, reports）
│   └── pubspec.yaml            # Flutter 依赖
└── docs/                       # 项目文档与记忆系统
```

## 核心模块关系

```
用户操作                    后端处理链路
─────────                  ──────────────
上传曲谱 ──────────────▶  omr_parser ───▶ 标准 MIDI ───▶ DB(scores)
录制视频 ──────────────▶  hand_tracker ──▶ 手型异常列表
                          audio_amt ─────▶ 音准 diff 列表
                          ──── 组装 ──────▶ LLM 评语 ───▶ TTS 合成
                          ──── 写入 ──────▶ DB(practice_reports)
                          ◀── JSON + audio_url ── 返回前端
App 设置页 ────────────▶  config_manager ──▶ config.json（原子写入）
```
