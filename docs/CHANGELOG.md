# 变更日志

> 基于 Git 提交历史自动维护

格式基于 [Keep a Changelog](https://keepachangelog.com/)

---

## [Unreleased]

### Added
- [2026-05-28] 手型分析流水线 `backend/tests/analyze_hands.py`：视频抽帧 + 21 点 MediaPipe 红色骨架 + 四维度评分（折指/塌陷/过伸/拇指内扣）+ 最差 5 帧筛选
- [2026-05-28] GPU 诊断脚本 `backend/tests/test_gpu_oemer.py`：ONNX CUDA Provider 可用性检测

### Fixed
- [2026-05-28] 手型图片中文显示 `?`：改用 PIL + 微软雅黑（msyh.ttc）渲染中文标注，替换 OpenCV putText
- [2026-05-28] 综合评估脚本 `backend/tests/run_full_evaluation.py`（4 阶段全链路：Oemer + 手型 + 音频 + DeepSeek 报告）
- [2026-05-28] 手型可视化：MediaPipe 骨架标注帧（问题帧 + 正常帧）
- [2026-05-28] 测试报告命名规范：`REPORT_YYYY-MM-DD_HHMM.md` 格式

### Changed
- [2026-05-28] `omr_parser.py` 合并 MIDI 改用 `pretty_midi` 库（修复手写 binary MIDI 格式损坏）
- [2026-05-28] ONNX GPU 加速配置：安装 `nvidia-cudnn-cu12`（cuDNN 9.22），脚本启动注册 DLL 路径
- [2026-05-28] hand_tracker.py 降低检测阈值（conf 0.5→0.3, PIP 80°→100°），提升检出率

### Fixed
- [2026-05-28] 修复 conda run 管道 GBK 编码错误（改用 Python 解释器直接运行）
- [2026-05-28] 修复 Oemer MusicXML 音符音高越界（clamp 至 MIDI 0-127）
- [2026-05-28] 修复 numpy int64 JSON 序列化错误（自定义 NumpyEncoder）

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
