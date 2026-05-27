# 技术决策记录

> 记录所有重要的技术决策，确保项目方向一致

---

## [2026-05-25] 数据库选型：SQLite

**决策**：MVP 阶段使用 SQLite 3 + SQLAlchemy 2.x

**为什么**：
- 本地文件数据库，无需额外运维
- MVP 阶段用户量小，SQLite 完全够用
- SQLAlchemy 抽象层使后续迁移到 PostgreSQL 只需改一个 URL

**备选方案**：PostgreSQL（后续上量时切换）

---

## [2026-05-25] LLM 协议：OpenAI 兼容 API

**决策**：所有 LLM 调用统一使用 OpenAI 兼容的 chat.completions 协议

**为什么**：
- OpenAI 兼容协议是行业事实标准
- DeepSeek / 通义 / 智谱 / Kimi / Ollama 等国内主流服务均支持
- 用户只需改 base_url + api_key 即可切换模型
- 一套代码覆盖所有 LLM 供应商

---

## [2026-05-25] AI 模型 Mock 策略

**决策**：所有 AI 模型（手型/音频/曲谱识别）提供 Mock 实现，可一键切换真实模型

**为什么**：
- MVP 阶段优先跑通端到链路
- 真实模型依赖重（MediaPipe、PyTorch 等），开发环境搭建成本高
- Mock 使 Demo 演示不受模型可用性影响
- 比赛评审时可选择性展示真实效果

---

## [2026-05-25] 部署方式：局域网部署

**决策**：PC 运行后端 + 手机 App 通过局域网连接

**为什么**：
- 避免云服务器成本
- 比赛 Demo 场景足够
- 降低延迟（视频传输不需要公网带宽）

---

## [2026-05-26] 音频转录选型：basic-pitch 替代 ByteDance Piano Transcription

**决策**：使用 Spotify basic-pitch（ONNX 后端）替换原计划的 ByteDance Piano Transcription。

**为什么**：
- basic-pitch 轻量（ONNX 推理 ~200MB），ByteDance 方案需 PyTorch 全家桶
- ONNX 后端与 Oemer 复用同一运行时，减少环境冲突
- 预训练模型可用，支持多音高检测（polyphonic）
- Apache 2.0 开源协议友好

**备选方案**：保持 TensorFlow 后端（basic-pitch 也支持），但 ONNX 更轻

---

## [2026-05-26] 虚拟环境迁移：Python venv → Conda

**决策**：从 `backend/.venv` 迁移到 Conda 环境 `AIqinban`（Python 3.11）。

**为什么**：
- basic-pitch 官方只支持 Python 3.8-3.11，.venv 的 Python 3.12 不兼容
- Conda 更便于管理 C++ 依赖（MediaPipe、ONNX Runtime）
- Conda 独立环境方便后续 CosyVoice（PyTorch）隔离

---

## [2026-05-26] 所有 AI 模型统一 Mock 兜底策略

**决策**：4 个 AI 模块（hand_tracker / audio_amt / omr_parser / tts_engine）统一采用"真实模型优先 + 异常回退 Mock"模式。

**为什么**：
- 确保整条链路在任何环境下都能跑通
- 模型环境未就绪时不影响 Demo 展示
- 每个模块的 Mock 异常只触发一次（模块级 _MOCK_FALLBACK 标记），避免反复重试
- TTS 的 CosyVoice 失败时自动回退 edge-tts

---

## [2026-05-28] 综合测试报告命名规范

**决策**：测试报告文件使用 `REPORT_YYYY-MM-DD_HHMM.md` 格式命名，保存在 `backend/tests/` 目录下。

**为什么**：
- 日期+时间命名可追溯每次测试的时间点，便于对比不同批次的评估结果
- 放在 tests/ 目录下与测试脚本同目录，方便查找
- 避免同名文件覆盖历史报告

---

## [2026-05-28] ONNX GPU 加速配置

**决策**：通过 pip 安装 `nvidia-cudnn-cu12` 包（而非手动下载 cuDNN），并在脚本启动时通过 `os.add_dll_directory()` 注册 DLL 路径。

**为什么**：
- pip 安装方式比手动配置环境变量更可重复、更自动化
- `os.add_dll_directory()` 在 Python 3.8+ 是标准做法，不依赖系统 PATH
- cuDNN 9.22 配合 CUDA 12.9 / ONNX Runtime 1.26 在 RTX 5070 上可用
