# 项目进度

> 最后更新：2026-05-28

## 进行中

- [ ] 分支管理：切回 `develop` 分支进行日常开发（当前在 `master`）
- [ ] 端到端联调测试（视频上传 → 手型+音频分析 → 评语 → TTS → 报告）

## 待办

- [ ] CosyVoice 环境配置（独立 conda 环境 `AIqinban-models`）
- [ ] 用户鉴权完善（当前为占位实现）
- [ ] Flutter Web 联调与 UI 细节优化
- [ ] Demo 视频录制（30秒展示视频）
- [ ] 数字人形象优化（Lottie 动画替换）

## 已完成

- [x] [2026-05-25] 项目记忆系统初始化
- [x] [2026-05-25] 创建 docs/ 目录及全部记忆文件
- [x] [2026-05-25] 创建 .gitignore
- [x] [2026-05-25] HTML 交互原型 Demo
- [x] [2026-05-25] Flutter Web 兼容改造（条件导入三件套）
- [x] [2026-05-25] UI 全面重设计（home/feedback/practice/avatar_2d）
- [x] [2026-05-25] 确认项目代码完整性
- [x] 后端 FastAPI 框架搭建（main.py + 路由模块）
- [x] 数据库模型设计（users / scores / practice_reports）
- [x] 配置中心 API（用户自定义 LLM/TTS）
- [x] 多模态评估 API（视频上传 → 分析 → 评语 → TTS → 返回）
- [x] Flutter 前端框架搭建（screens / widgets / services / models）
- [x] App 设置页（LLM/TTS 配置 + 连通性测试）
- [x] 文档编写（README / API.md / DATABASE.md）
- [x] [2026-05-26] 迁移到 Conda 环境 `AIqinban`（Python 3.11）
- [x] [2026-05-26] **接入真实 MediaPipe Hands**（hand_tracker.py：21 点关键点 + 折指/掌关节塌陷检测，Mock 兜底）
- [x] [2026-05-26] **接入 basic-pitch**（audio_amt.py：ONNX 后端音频转录 + MIDI diff 比对，Mock 兜底）
- [x] [2026-05-26] **接入 Oemer OMR**（omr_parser.py：CLI 调用 + MusicXML→MIDI 转换，Mock 兜底）
- [x] [2026-05-26] **CosyVoice TTS 桥接**（tts_engine.py + cosyvoice_bridge.py：子进程调用 + edge-tts 兜底）
- [x] [2026-05-26] 更新 CLAUDE.md（Conda 环境规范）
- [x] [2026-05-26] 更新 requirements.txt（完整依赖列表）
- [x] [2026-05-26] **后端启动成功**：删除冗余 `.venv`，确认 Conda `AIqinban` 环境正常运行
- [x] [2026-05-27] **ffmpeg 已安装**（v8.1.1），音频提取可用
- [x] [2026-05-27] **测试素材就绪**：`test.mp4`（弹琴视频）+ `1.jpg/2.jpg/3.jpg`（曲谱 3 页）放入 `backend/test_data/`
- [x] [2026-05-27] `backend/test_data/` 加入 .gitignore
- [x] [2026-05-28] **Oemer ONNX 环境验证通过**：3 页曲谱解析成功，合并 MIDI 911 音符/71 小节
- [x] [2026-05-28] **cuDNN 9.22 安装**：ONNX GPU (CUDA 12.9) 可用，RTX 5070 已注册
- [x] [2026-05-28] **综合评估脚本**：`backend/tests/run_full_evaluation.py` 完成
- [x] [2026-05-28] **DeepSeek v4-pro 报告生成**：手型 34 问题 + 音频 diff + 专家建议 → `backend/tests/COMPREHENSIVE_REPORT.md`
- [x] [2026-05-28] **手型可视化**：17 张问题帧 + 6 张正常帧，MediaPipe 骨架标注
- [x] [2026-05-28] **手型分析流水线**：`backend/tests/analyze_hands.py` — 视频抽帧 + 21点红色骨架 + 四维度评分 + 最差5帧
- [x] [2026-05-28] **ONNX GPU 诊断**：`backend/tests/test_gpu_oemer.py` — 确认 CUDAExecutionProvider 可用，RTX 5070 已识别
- [x] [2026-05-28] **手型图片中文渲染**：修复 OpenCV putText 中文显示 `?`，改用 PIL + 微软雅黑字体渲染
- [x] [2026-05-28] **弹奏姿势过滤**：三条件过滤排除非弹奏状态误检（手腕位置/手指张开/手部面积）
- [x] [2026-05-28] **新测试数据 test2**：35s 横屏视频（1280x720）+ 2 页曲谱，手型分析已跑通
