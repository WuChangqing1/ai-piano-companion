# 项目进度

> 最后更新：2026-05-25
> 本文件由 Agent 自动初始化

## 进行中

- [ ] 确认项目代码完整性，排查缺失功能

## 待办

- [ ] 初始化 git 仓库并推送到远程
- [ ] 接入真实 MediaPipe 手型检测（替换 Mock）
- [ ] 接入 ByteDance Piano Transcription（替换 Mock）
- [ ] 接入 Oemer OMR 曲谱识别（替换 Mock）
- [ ] 实现 CosyVoice TTS 引擎
- [ ] 用户鉴权完善（当前为占位实现）
- [ ] 数字人形象优化（Lottie 动画替换）

## 已完成

- [x] [2026-05-25] 项目记忆系统初始化
- [x] [2026-05-25] 创建 docs/ 目录及全部记忆文件
- [x] [2026-05-25] 创建 .gitignore
- [x] 后端 FastAPI 框架搭建（main.py + 路由模块）
- [x] 数据库模型设计（users / scores / practice_reports）
- [x] AI 模型模块 Mock 实现（hand_tracker / audio_amt / omr_parser / llm_client / tts_engine）
- [x] 配置中心 API（用户自定义 LLM/TTS）
- [x] 多模态评估 API（视频上传 → 分析 → 评语 → TTS → 返回）
- [x] Flutter 前端框架搭建（screens / widgets / services / models）
- [x] App 设置页（LLM/TTS 配置 + 连通性测试）
- [x] 文档编写（README / API.md / DATABASE.md）
