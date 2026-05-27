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

## 2026-05-25 会话（状态检测与文档更新）

**做了什么**：
- 检测项目当前状态（git、分支、未跟踪文件、虚拟环境、文档完整性）
- 更新 PROGRESS.md：调整"进行中"任务（移动已完成项、新增分支管理任务）
- 更新 ISSUES.md：记录分支管理问题（当前在 master 而非 develop）
- 发现 `frontend_app/` 大量文件未跟踪，`start_backend.bat` / `start_flutter_web.bat` 未提交

**当前状态摘要**：
- 分支：`master`（领先 origin/master 1 commit，需合并到 develop）
- 未跟踪：frontend_app/.gitignore, .metadata, README.md, analysis_options.yaml, android/, assets/, pubspec.lock, test/, web/, start_backend.bat, start_flutter_web.bat
- 虚拟环境：backend/.venv 正常
- 文档：7 个记忆文件完整

**下一步建议**：
- 将 master 的 commit 合并到 develop，切回 develop 开发
- 将未跟踪的项目文件加入 git 并提交
