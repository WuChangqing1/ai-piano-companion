# 变更日志

> 基于 Git 提交历史自动维护

格式基于 [Keep a Changelog](https://keepachangelog.com/)

---

## [Unreleased]

### Added
- [2026-05-28] **统一流水线脚本** `backend/tests/run_full_pipeline.py`：预检机制 + 5 阶段自动执行（Oemer → 手型 → 音频转录 → 比对 → HTML 报告）
- [2026-05-28] **HTML 综合报告** `backend/tests/generate_html_report.py`：专业 CSS 样式 + base64 内嵌图片 + 响应式布局，适配 Flutter WebView
- [2026-05-28] 音频转录脚本 `backend/tests/run_audio_transcribe.py`：basic-pitch ONNX 模型，视频音频 → MIDI
- [2026-05-28] 音频比对脚本 `backend/tests/compare_audio.py`：自动时间对齐 + 错音/漏音/多余音检测 + 节奏分析 + 评分
- [2026-05-28] 手型分析流水线 `backend/tests/analyze_hands.py`：视频抽帧 + 21 点 MediaPipe 红色骨架 + 四维度评分（折指/塌陷/过伸/拇指内扣）+ 最差 5 帧筛选
- [2026-05-28] GPU 诊断脚本 `backend/tests/test_gpu_oemer.py`：ONNX CUDA Provider 可用性检测

### Fixed
- [2026-05-28] **严重：MusicXML→MIDI 转换遗漏真实 tempo**：添加 `_read_musicxml_tempo()` 从 `<sound tempo="X"/>` 标签读取实际 BPM，修复硬编码 120 BPM 导致的时序错误。经验证 test3 标准 MIDI 正确从 ~115s→153s
- [2026-05-28] 修复 `run_full_pipeline.py` ffprobe 输出解析：改为 `-select_streams v:0` 单独查询视频流，避免多流输出混淆
- [2026-05-28] 修复所有 subprocess 调用的 GBK 编码问题：统一 `encoding='utf-8', errors='replace'`
- [2026-05-28] 手型图片中文显示 `?`：改用 PIL + 微软雅黑（msyh.ttc）渲染中文标注，替换 OpenCV putText
- [2026-05-28] 修复 conda run 管道 GBK 编码错误（改用 Python 解释器直接运行）
- [2026-05-28] 修复 Oemer MusicXML 音符音高越界（clamp 至 MIDI 0-127）
- [2026-05-28] 修复 numpy int64 JSON 序列化错误（自定义 NumpyEncoder）

### Changed
- [2026-05-28] **报告格式从 Markdown 改为 HTML**：更好的 WebView 兼容性，专业视觉呈现
- [2026-05-28] `analyze_hands.py` 支持命令行指定输出目录参数
- [2026-05-28] `omr_parser.py` 合并 MIDI 改用 `pretty_midi` 库（修复手写 binary MIDI 格式损坏）
- [2026-05-28] ONNX GPU 加速配置：安装 `nvidia-cudnn-cu12`（cuDNN 9.22），脚本启动注册 DLL 路径
- [2026-05-28] hand_tracker.py 降低检测阈值（conf 0.5→0.3, PIP 80°→100°），提升检出率

### Added
- [2026-05-25] HTML 交互原型 Demo（`demo/AI琴伴Demo.html`）：手机边框、6页面、数字人动画、雷达图、评分仪表盘
- [2026-05-25] Flutter Web 条件导入架构（`recorder.dart` + `recorder_mobile.dart` + `recorder_web.dart`）
- [2026-05-25] 初始化项目记忆系统（docs/ 目录 + 6 个记忆文件）
- [2026-05-25] 创建 .gitignore（Python / Flutter / IDE / 敏感文件）
- [2026-05-25] 后端 FastAPI 框架（路由、数据库、AI Mock、配置中心）
- [2026-05-25] Flutter 前端框架（页面、组件、API 客户端、设置页）
- [2026-05-25] 项目文档（README / API.md / DATABASE.md）

### Added
- [2026-05-25] 提交 Flutter 前端项目文件（`frontend_app/`）+ 一键启动脚本（`start_backend.bat` / `start_flutter_web.bat`）

### Fixed
- [2026-05-26] 修复后端启动报错：删除冗余 `.venv`，统一使用 Conda `AIqinban` 环境

### Changed
- [2026-05-25] `practice_screen.dart` 全面重写：移除 CameraPreview 直接依赖，添加钢琴键模拟视图 + Mock 数据回退
- [2026-05-25] `home_screen.dart` UI 重设计：渐变头部、曲谱卡片、淡入动画
- [2026-05-25] `feedback_screen.dart` 完整重写：圆环评分、雷达图、打字机评语、问题列表、数字人
- [2026-05-25] `avatar_2d.dart` 重写：齐刘海波波头、眨眼、嘴巴开合、说话发光效果
- [2026-05-25] `app_config.dart` 默认 URL 改为 `http://localhost:8000`
