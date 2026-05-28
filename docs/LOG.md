# 会话日志

> 每次会话结束前追加一条记录

---

## 2026-05-25 会话

**做了什么**：
- 初始化项目记忆系统
- 创建 docs/ 目录及全部记忆文件（ARCHITECTURE / PROGRESS / DECISIONS / ISSUES / LOG / CHANGELOG）
- 创建 .gitignore（Python + Flutter + IDE + 敏感文件）
- 初始化 git 仓库并完成首次提交

**下次继续**：
- 确认项目代码完整性，排查缺失功能
- 根据用户需求决定下一步开发方向

---

## 2026-05-25 会话（续）

**做了什么**：
- 创建 HTML 交互原型 Demo（`demo/AI琴伴Demo.html`）
  - 手机边框（Phone Frame）展示，模拟真实手机屏幕
  - 6 个完整页面：首页、录制、加载、反馈、历史、设置
  - 2D 数字人 SVG 组件（说话时嘴巴开合动画、眨眼）
  - SVG 雷达图（节奏/音准/流畅度/手型 四维）
  - 圆环评分仪表盘（动画填充）
  - 打字机效果的教师评语
  - 脉冲录制按钮 + 波形加载动画
  - 底部 Tab 导航 + 页面切换动画
- Flutter Web 兼容改造
  - 创建条件导入三件套：`recorder.dart` + `recorder_mobile.dart` + `recorder_web.dart`
  - 重写 `practice_screen.dart`：移除 CameraPreview 直接依赖，添加钢琴键模拟视图
  - 添加 Web 平台文件：`flutter create . --platforms=web`
  - Mock 数据回退：API 调用失败时使用内置示例数据
- UI 全面重设计（参考阿里设计理念 + Claude Design System）
  - `home_screen.dart`：渐变头部、曲谱卡片、操作按钮、小贴士卡片、淡入动画
  - `feedback_screen.dart`：渐变头部+数字人、圆环评分、打字机评语、雷达图、指标网格、问题列表
  - `avatar_2d.dart`：齐刘海波波头、眨眼、嘴巴开合、发光说话效果、浮动音符
  - `practice_screen.dart`：模拟钢琴键背景、REC指示器+脉冲、停止按钮发光
- 启动后端（port 8000）+ Flutter Web（Chrome port 3000）
- 修改 `app_config.dart` 默认 URL 为 `http://localhost:8000`

**下次继续**：
- Flutter Web 联调UI细节
- 录制 30 秒 Demo 视频
- 接入真实 AI 模型替换 Mock

---

## 2026-05-26 会话

**做了什么**：
- 排查后端启动报错 `ModuleNotFoundError: No module named 'aiofiles'`
- 定位根因：`backend/.venv`（Python 3.12）被自动激活，覆盖 Conda `AIqinban` 环境
- 删除冗余 `.venv`，确认 Conda `AIqinban` 中所有依赖正确安装
- 验证后端正常启动：`/` 返回服务信息和版本号，`/docs` 返回 Swagger API 文档

**git commit**: `3e7a2e7`

---

## 2026-05-26 会话（AI 模型真实接入）

**做了什么**：
- 创建 Conda 环境 `AIqinban`（Python 3.11），安装全部依赖
- **接入 basic-pitch**：重写 `audio_amt.py`，ONNX 后端音频转录 + MIDI diff 比对（错音/漏音/多余音 + 节奏评分）
- **启用 MediaPipe Hands**：`hand_tracker.py` 设置 `USE_REAL_MODEL=True`，完善五指独立识别（折指 + 掌关节塌陷）
- **接入 Oemer**：重写 `omr_parser.py`，CLI 调用 + MusicXML→MIDI 转换
- **CosyVoice 桥接**：新建 `cosyvoice_bridge.py`，子进程调用 + edge-tts 自动回退
- 解决 basic-pitch + Python 3.12 不兼容问题 → 迁移到 Conda Python 3.11
- 解决 numpy 版本冲突（TensorFlow vs opencv）→ 卸载 TF，basic-pitch 走 ONNX
- 更新 CLAUDE.md（Conda 环境规范）
- 更新 requirements.txt（完整依赖列表）
- 更新 docs/（ARCHITECTURE / PROGRESS / DECISIONS）
- 创建 docs/ToDo.md（用户下一步操作清单）

**下一步**：
- 安装 ffmpeg
- 准备测试素材（弹钢琴视频 + 曲谱图片）
- 逐模块测试（手型 → 音频 → 曲谱 → 全链路）
- 切回 `develop` 分支

---

## 2026-05-28 会话（综合测试评估）

**做了什么**：
- 验证 Oemer ONNX 环境：3 页曲谱全部解析成功（合并 MIDI 911 音符 / 71 小节）
- 安装 cuDNN 9.22（`nvidia-cudnn-cu12`），注册 GPU DLL 目录，ONNX CUDA Provider 可用
- 编写 `backend/tests/run_full_evaluation.py` 综合评估脚本：
  - 阶段 1：Oemer 曲谱解析 + pretty_midi 合并标准 MIDI
  - 阶段 2：MediaPipe Hands 手型检测 + 骨架可视化（23 张标注帧）
  - 阶段 3：basic-pitch 音频转录 + 与标准 MIDI 逐音符比对（838 vs 911 音符）
  - 阶段 4：DeepSeek v4-pro API 生成中文评估报告
- DeepSeek API 配置：Windows 环境变量 `DeepSeek`，模型 `deepseek-v4-pro`
- 生成 `backend/tests/COMPREHENSIVE_REPORT.md`：
  - 手型：34 个问题（折指 16 + 掌关节塌陷 18），中指/无名指是高发区
  - 音准：正确率 38.5%（351/911），错音 487，漏音 560
  - 节奏：60 分，tempo 448.7 BPM
  - 含 5 条可执行练习建议
- 更新 PROGRESS.md / ISSUES.md

**git commit**: `b1a81c7`

**下次继续**：
- 查看手型标注帧图片，确认 MediaPipe 检测质量
- 验证 ONNX GPU 实际加速效果（当前 Oemer 走缓存跳过）
- 端到端 Swagger 联调测试
- 切回 develop 分支

---

## 2026-05-28 会话（手型分析流水线）

**做了什么**：
- 确认 ONNX Runtime CUDA Provider 可用（RTX 5070 + cuDNN 9.22），Oemer 无需 TensorFlow
- 编写 `backend/tests/analyze_hands.py` 手型分析流水线：
  - 视频每 0.5s 抽帧，MediaPipe Hands 21 点关键点检测
  - 红色骨架连线绘制（问题手指亮橙黄加粗标注）
  - 四维度评分：折指（PIP<90°）、掌关节塌陷（MCP低于PIP>0.01）、过度伸直（PIP>178°）、拇指内扣
  - 最差 5 帧自动筛选 + 输出
- 编写 `backend/tests/test_gpu_oemer.py` GPU 诊断脚本
- 测试视频 test.mp4（113s）分析结果：226 帧，225 帧检测到手，平均分 95/100，208 个问题
- 最差 5 帧：t=87.0s(40分)、t=76.5s(59分)、t=95.0s(65分)、t=113.0s(68分)、t=24.5s(72分)
- 输出目录：`test_data/hand_analysis_report/`（报告 + 数据 JSON + 全部帧 + 最差 5 帧）
- 更新 PROGRESS.md / CHANGELOG.md / LOG.md

**git commit**: `6e53e51`

**补充**: `de68cc8` — 修复手型图片中文渲染（OpenCV → PIL + 微软雅黑）

---

## 2026-05-28 会话（HTML 报告 + 统一流水线 + tempo bug 修复）

**做了什么**：
- 将综合报告格式从 Markdown 改为 HTML（`backend/tests/generate_html_report.py`）：
  - 专业 CSS 样式：渐变头部、评分卡片、四维指标网格、响应式布局
  - base64 内嵌手型骨架图，单文件自包含
  - 支持命令行参数指定测试目录
  - 适配 Flutter WebView 直接渲染
- 编写 `backend/tests/run_full_pipeline.py` 统一流水线脚本：
  - 预检机制（pre-flight checks）：视频元数据、曲谱页数、音频轨道、Python 依赖、Oemer CLI
  - 5 阶段自动执行：Oemer OMR → 手型分析 → 音频转录 → 比对 → HTML 报告
- **发现并修复严重 bug**：MusicXML→MIDI 转换遗漏真实 tempo
  - 根因：`omr_parser.py` 硬编码 120 BPM，忽略 MusicXML 的 `<sound tempo="90"/>` 标签
  - test3 实际速度 90 BPM，生成的 MIDI 错误使用 120 BPM，导致 105.9 vs 192.5 BPM 的巨大差异
  - 修复：`_read_musicxml_tempo()` 从 MusicXML 读取实际 BPM，`beat_duration = 60.0 / tempo`
- test3 数据跑通：81.5s 竖屏视频，1 页曲谱（90 BPM），手型分析 162 帧/平均分 90
- 更新全部 docs/ 文档（ISSUES / DECISIONS / PROGRESS / CHANGELOG / ARCHITECTURE / LOG）
- 分析 `analyze_hands.py` 支持输出目录参数

---

## 2026-05-28 会话（test3 流水线重新运行 + 验证）

**做了什么**：
- 修复 `run_full_pipeline.py` 的 ffprobe 输出解析：改为按视频流单独查询，解决多流输出混淆问题
- 修复所有 subprocess 调用的 GBK 编码问题：统一使用 `encoding='utf-8', errors='replace'`
- **重新运行 test3 流水线验证 tempo 修复**：
  - Stage 1: Oemer 成功，标准 MIDI 153s @ 90 BPM（正确！之前是 115s @ 120 BPM）
  - Stage 2: 手型分析 162 帧，平均分 90/100，199 个问题
  - Stage 3: basic-pitch 转录 309 音符
  - Stage 4: 音频比对 — 时间匹配 113 音符（正确 19，错音 94，漏音 82，多余音 196）
  - Stage 5: HTML 报告生成 1206 KB
- 分析比对结果：低分原因主要是弹奏速度不匹配（153s 曲谱 vs 81s 视频）+ basic-pitch 八度误识别
- 更新 docs/ 文档

**git commit**: `5d0b1cd`

**下次继续**：
- 将 tempo 读取逻辑回迁到 `omr_parser.py` 生产代码
- 考虑音频比对加入八度容忍（octave-invariant comparison）
- 切回 `develop` 分支

---

## 2026-05-29 会话（CosyVoice TTS 接入 + 端到端语音报告）

**做了什么**：
- **CosyVoice HTTP API 接入**：改用 CosyVoice_For_Windows 的 Flask API（端口 9880），不再需要复制 3GB 模型文件夹
  - 更新 `tts_engine.py`：新增 `synthesize_sync()` 同步方法，`_synthesize_cosyvoice()` 改用 `requests` 调 HTTP API
  - 更新 `config.json`：engine 改为 `cosyvoice`，新增 `cosyvoice_url/speaker/speed` 配置项
  - 保留 edge-tts 兜底（CosyVoice 不可用时自动回退）
- **流水线增加 TTS 阶段**（`run_full_pipeline.py`）：
  - `_build_tts_text()`：根据手型/音频/综合分数生成温暖鼓励的老师点评文本
  - `synthesize_tts()`：调用 CosyVoice API 合成音频（~933KB WAV，~22s）
  - HTML 报告新增「老师点评语音」卡片：`<audio>` 播放器 + JavaScript 自动播放 + 播放完毕提示
- **端到端验证**：test3 全流程跑通（Oemer → 手型 → 音频转录 → 比对 → TTS → HTML 报告，27s）

**git commit**: `e411caa`

**下次继续**：
- 将 tempo 读取逻辑回迁到 `omr_parser.py` 生产代码
- 切回 `develop` 分支




