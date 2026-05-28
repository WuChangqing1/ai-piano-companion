# 项目进度

> 最后更新：2026-05-29

## 进行中

- [ ] **APK 真机测试**：相机录制 + 上传 PC 后端 + 报告查看 + 音频播放器验证
- [ ] 端到端联调测试（视频上传 → 手型+音频分析 → 评语 → TTS → 报告）

## 待办

- [ ] **Android 正式发布**：release 签名配置 + `flutter build apk --release`（当前仅有 debug APK 148MB）
- [ ] 分支管理：切回 `develop` 分支进行日常开发
- [ ] 用户鉴权完善（当前为占位实现）
- [ ] Demo 视频录制（30秒展示视频）
- [ ] 数字人形象优化（Lottie 动画替换）
- [ ] MusicXML→MIDI 使用 `divisions` 元素做精确时序（替代简化的 type→duration 映射）
- [ ] MusicXML→MIDI tempo 读取逻辑回迁到生产代码 `omr_parser.py`
- [ ] 报告 `skipped_by_filter` 格式化显示（当前显示为 dict repr）
- [ ] basic-pitch 转录准确率验证（播放转录 MIDI 对比原音频）

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
- [x] [2026-05-28] **basic-pitch 音频转录**：ONNX 模型，test2 音频 → MIDI（377 音符）
- [x] [2026-05-28] **音频比对修正**：自动时间对齐（1.15s 起始偏移），144 个时间匹配音符
- [x] [2026-05-28] **综合评估报告**：`test2/COMPREHENSIVE_REPORT.md`（1.5MB，含 5 张 base64 手型骨架图 + 手型分析 + 音频比对 + 练习建议）
- [x] [2026-05-28] **报告格式改为 HTML**：`backend/tests/generate_html_report.py` — 专业 CSS 样式 + base64 内嵌图片 + 响应式布局，适配 Flutter WebView
- [x] [2026-05-28] **统一流水线脚本**：`backend/tests/run_full_pipeline.py` — 预检 + 5 阶段自动执行（Oemer → 手型 → 音频转录 → 比对 → HTML 报告）
- [x] [2026-05-28] **修复 MusicXML→MIDI tempo 读取 bug**：`_read_musicxml_tempo()` 从 `<sound tempo="X"/>` 标签读取实际 BPM（之前硬编码 120 BPM 导致 test3 比对完全错误）
- [x] [2026-05-28] **test3 数据测试**：81.5s 竖屏视频 + 1 页曲谱（tempo=90），手型分析已跑通（162 帧，平均分 90/100）
- [x] [2026-05-28] **test3 流水线重新运行验证**：tempo bug 修复后全流程跑通（标准 MIDI 153s@90BPM，手型 90/100，HTML 报告 1206KB）
- [x] [2026-05-29] **CosyVoice TTS 接入**：HTTP API 方式调用 CosyVoice_For_Windows（端口 9880），无需复制模型。流水线自动生成老师语音点评（~22s），HTML 内嵌 `<audio>` 播放器，支持自动播放 + 播放完毕自动停止
- [x] [2026-05-29] **PC + Android 双端 Demo**：Demo.html 全面改造（去 AI 化、真实 API、CosyVoice 音色选择、emoji 图标、audio controls 播放器）
- [x] [2026-05-29] **后端路由扩展**：`/demo` 路由（PC 浏览器演示页）、`/api/cosyvoice/speakers` 代理（手机端获取 CosyVoice 音色列表）
- [x] [2026-05-29] **Flutter Android APK 壳**：WebView 加载 Demo.html + JavaScriptChannel 桥接 + 原生相机录制 + Dio 上传后端
- [x] [2026-05-29] **PC 一键演示脚本** `demo_pc.bat`：自动检查后端 + CosyVoice + 执行流水线 + 打开浏览器
- [x] [2026-05-29] **PC Demo 手型图片展示**：API 评估链路接入完整手型分析（21点骨架标注 + base64 图片 + 最差5帧展示），Demo 反馈页新增手型详情卡片（问题类型分布 + 每帧骨架标注图）
- [x] [2026-05-29] **Demo 页细节优化**：老师头像替换为 `teacher_avatar.png`、品牌名统一为"AI琴伴"、帧卡片标题精简
- [x] [2026-05-29] **Android APK 构建成功**：移除冲突的 `file_picker` 依赖（WebView 架构已不需要），配置 Gradle 国内镜像源 + Kotlin 增量编译禁用，`app-debug.apk`（148MB）输出成功
