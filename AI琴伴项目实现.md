# AI 琴伴 — 项目完整实现计划

> 最后更新：2026-05-25
> 基于全量代码审查生成，覆盖后端 + 前端 + AI 模型 + 部署

---

## 当前状态总览

| 层面 | 完成度 | 说明 |
|------|--------|------|
| 后端框架 | 70% | FastAPI 骨架完整，路由/数据库/配置中心可用 |
| AI 模型层 | 10% | 全部 Mock，仅 hand_tracker 有真实代码 stub |
| 前端 UI | 65% | 5 个页面均有业务逻辑，但有崩溃 Bug 和功能缺失 |
| 测试 | 0% | 无任何自动化测试 |
| 部署 | 0% | 无 Dockerfile、无 CI/CD |

---

## 第一阶段：修复崩溃 Bug + 功能补全（优先级最高）

> 目标：让现有代码稳定运行，不新增功能

### 1.1 后端 Bug 修复

| # | 文件 | 问题 | 修复方案 |
|---|------|------|----------|
| 1 | `api/evaluate.py` | `score_id` 接收但从未使用，报告不关联曲谱 | 查库将 score_uid 转为 id，写入 PracticeReport |
| 2 | `api/config.py` | `reveal=True` 暴露明文 API Key，无鉴权 | 添加简单 token 鉴权，或移除 reveal 参数 |
| 3 | `api/score.py` | 无文件大小限制，大文件可 OOM | 添加 UploadFile 大小校验（如 10MB 上限） |
| 4 | `api/evaluate.py` | 无视频文件大小限制 | 添加分块读取大小计数器，超 200MB 拒绝 |
| 5 | `ai_models/llm_client.py` | 每次调用创建新 AsyncOpenAI 客户端，连接池不复用 | 改为模块级单例 + `await client.close()` |
| 6 | `ai_models/llm_client.py` | `except Exception` 静默吞掉所有异常，无法调试 | 添加 `logger.exception()` 日志 |
| 7 | `ai_models/hand_tracker.py` | `_real_detect` 未关闭 MediaPipe Hands，资源泄漏 | 使用 `with mp_hands.Hands(...) as hands` |
| 8 | `main.py` | `allow_origins=["*"]` + `allow_credentials=True` 违反 CORS 规范 | 改为具体域名列表，或去掉 credentials |
| 9 | `db/models.py` | `datetime.utcnow` 在 Python 3.12+ 已弃用 | 改为 `datetime.now(timezone.utc)` |
| 10 | `api/reports.py` | `json.loads(r.raw_json)` 在 raw_json 为 NULL 时崩溃 | 添加空值保护 `json.loads(r.raw_json or '{}')` |
| 11 | `api/reports.py` | 列表接口缺少 `fluency_score` 字段 | 补充返回 |
| 12 | `core/schemas.py` | Pydantic 模型定义了但 API 层未强制使用为 response_model | 为所有端点添加 `response_model` |

### 1.2 前端 Bug 修复

| # | 文件 | 问题 | 修复方案 |
|---|------|------|----------|
| 1 | `feedback_screen.dart` | `onPlayerComplete.listen()` 每次 `_play()` 新增 listener，不释放 | listener 移到 `initState`，保存 subscription 在 `dispose` 中取消 |
| 2 | `settings_screen.dart` | `_test()` 无 try/catch，网络错误时崩溃 | 包裹 try/catch，显示友好错误信息 |
| 3 | `report.dart` | `fromJson` 硬类型转换，后端返回 null 时 TypeError | 所有字段加 `?? 默认值` 或 `as Type?` |
| 4 | `model_config.dart` | 同上硬类型转换问题 | 同上 |
| 5 | `api_client.dart` | 每次请求创建新 Dio 实例，无连接池 | 改为 `late final` 单例，baseUrl 变化时重建 |
| 6 | `avatar_2d.dart` | AnimationController 在 `speaking=false` 时仍持续运转 | 用 `didUpdateWidget` 控制 start/stop |
| 7 | `main.dart` | `PingFang SC` 字体未打包，Android 上静默回退 | 在 pubspec.yaml 声明字体或改用系统自适应方案 |
| 8 | `settings_screen.dart` | TTS 的 `rate`/`pitch` 和 LLM `provider` 无 UI 控件 | 补充输入框/下拉选择 |
| 9 | `practice_screen.dart` | 进入即录制，无倒计时/计时器/取消 | 添加 3 秒倒计时 + 录制计时器 + 返回按钮 |
| 10 | `reports_screen.dart` | 历史记录无法点击查看详情 | 添加 onTap → 跳转到 FeedbackScreen（从 API 拉详情） |

### 1.3 Android 权限实际写入

- [ ] 将 `AndroidManifest_snippet.txt` 中的权限**实际写入** `android/app/src/main/AndroidManifest.xml`
- [ ] 添加 `android:usesCleartextTraffic="true"`
- [ ] iOS `Info.plist` 添加相机/麦克风/HTTP 权限说明
- [ ] 更新 `READ_EXTERNAL_STORAGE` → Android 13+ 细粒度权限

---

## 第二阶段：后端功能完善

> 目标：补全业务逻辑，让系统真正可用

### 2.1 用户鉴权（当前为零）

- [ ] 实现 JWT token 鉴权（登录返回 token，后续请求携带）
- [ ] 添加 auth 中间件，保护需要登录的接口
- [ ] 修复 `auth.py`：phone 和 open_id 都为 None 时拒绝创建用户
- [ ] 添加请求频率限制（防止刷接口）

### 2.2 文件管理

- [ ] 上传文件大小限制（曲谱 10MB / 视频 200MB）
- [ ] 上传失败时清理磁盘上的孤立文件
- [ ] TTS 音频文件定期清理（static/ 目录无限增长）
- [ ] 上传进度回调（大文件时前端显示进度条）

### 2.3 评估链路完善

- [ ] `score_id` 正确关联到 PracticeReport
- [ ] 评估失败时事务回滚（当前部分写入可能不一致）
- [ ] 添加评估超时机制（整体 120s 上限）
- [ ] 评估过程异步化（上传视频后立即返回 task_id，前端轮询结果）
- [ ] 添加 WebSocket 推送评估进度（可选优化）

### 2.4 报告增强

- [ ] 报告列表接口支持分页（offset + limit）
- [ ] 报告详情接口返回完整可视化数据
- [ ] 添加报告统计接口（平均分趋势、练习频率等）
- [ ] 支持报告导出为 PDF/图片（比赛 PPT 用）

---

## 第三阶段：AI 模型接入（核心工作量最大）

> 目标：将 Mock 替换为真实模型，需要独立的 `.venv-models` 虚拟环境

### 3.1 环境准备

- [ ] 创建 `backend/.venv-models` 虚拟环境
- [ ] 安装重型依赖：`torch`, `mediapipe`, `opencv-python`, `numpy`, `librosa`, `pretty_midi`
- [ ] 添加 GPU/CPU 自动检测
- [ ] 更新 `requirements-models.txt`

### 3.2 手型检测（MediaPipe）— 当前有 stub

**现有代码**：`hand_tracker.py` 中 `_real_detect()` 已写好框架

**需要完成**：
- [ ] 修复资源泄漏（使用 context manager）
- [ ] 检测所有 5 根手指的关节角度（当前只检测食指 5→6→7）
- [ ] 添加更多手型异常类型：
  - 折指（folded_finger）
  - 掌关节塌陷（collapsed_knuckle）
  - 手腕过低（low_wrist）
  - 手指过度张开（over_spread）
- [ ] 添加置信度阈值过滤
- [ ] 输出时间戳对齐到小节号
- [ ] 性能优化：跳帧策略调优

**预估工作量**：2-3 天

### 3.3 音频转录（AMT）— 当前无真实代码

**需要完成**：
- [ ] 从视频文件中提取音频（ffmpeg / moviepy）
- [ ] 接入 ByteDance Piano Transcription 或 `basic-pitch`（Spotify 开源）
- [ ] 将转录 MIDI 与标准 MIDI 对齐（DTW 算法）
- [ ] 实现 diff 逻辑：
  - 错音检测（音高不匹配）
  - 漏音检测（标准有但演奏没有）
  - 多余音检测（演奏有但标准没有）
  - 节奏评分（onset 时间偏差统计）
- [ ] 输出时间戳对齐到小节号

**备选方案**：
- `basic-pitch`（Spotify）：轻量，纯 Python，精度中等
- `piano_transcription`（ByteDance）：精度高，依赖 PyTorch
- `omnisart` / `mt3`：学术级，复杂度高

**预估工作量**：5-7 天

### 3.4 曲谱识别（OMR）— 当前无真实代码

**需要完成**：
- [ ] 接入 Oemer 或 Audiveris
- [ ] 图片预处理（灰度、二值化、倾斜校正）
- [ ] 输出标准 MusicXML → 转 MIDI
- [ ] 提取小节数、调号、拍号
- [ ] 处理多页 PDF

**备选方案**：
- Oemer：端到端深度学习，`pip install oemer`
- Audiveris：Java 工具，需 subprocess 调用
- 商业 API（如 Soundslice）：简单但有成本

**预估工作量**：3-5 天

### 3.5 LLM 评语优化

**当前状态**：可工作，但可改进

- [ ] 添加日志记录（当前异常被静默吞掉）
- [ ] 支持流式输出（SSE）让前端逐字显示评语
- [ ] 评语模板支持多语言
- [ ] 添加评语质量评估（长度、是否包含鼓励词等）
- [ ] 复用 AsyncOpenAI 客户端实例

### 3.6 TTS 引擎扩展

**当前状态**：edge-tts 可用，CosyVoice 为占位

- [ ] 实现 CosyVoice 接入（阿里通义开源 TTS）
- [ ] 添加 TTS 缓存（相同评语不重复合成）
- [ ] 音频文件定期清理

---

## 第四阶段：前端功能完善

### 4.1 用户体验提升

- [ ] 首页：添加欢迎页/引导页（首次使用）
- [ ] 录制页：3 秒倒计时 + 录制计时器 + 取消按钮
- [ ] 反馈页：添加"返回首页"按钮
- [ ] 历史页：点击条目跳转详情 + 下拉刷新
- [ ] 全局：添加加载动画（骨架屏）替代纯 CircularProgressIndicator
- [ ] 全局：网络错误统一提示（当前直接显示 Dio 异常堆栈）
- [ ] 设置页：未保存离开提醒

### 4.2 数据可视化

- [ ] 历史报告页添加分数趋势折线图（fl_chart 库）
- [ ] 练习时长统计
- [ ] 各维度分数雷达图
- [ ] 练习日历热力图

### 4.3 曲谱展示

- [ ] 上传曲谱后显示预览图
- [ ] 反馈页中高亮标注错误小节（在曲谱图上）
- [ ] 支持曲谱缩放/滚动查看

### 4.4 数字人升级

- [ ] 替换 CustomPainter 为 Lottie 动画
- [ ] 添加多种表情状态（开心/思考/鼓励）
- [ ] 评语文字同步显示（字幕效果）

---

## 第五阶段：测试

### 5.1 后端测试

- [ ] 单元测试：`config_manager.py`（读写、合并、掩码）
- [ ] 单元测试：`schemas.py`（验证边界值）
- [ ] 集成测试：API 端点（pytest + httpx TestClient）
  - `/api/config` 读/写/测试
  - `/api/upload_score` 正常 + 异常
  - `/api/evaluate` 端到端 Mock 链路
  - `/api/reports` 列表 + 详情
  - `/api/auth/login` 各种边界情况
- [ ] 数据库测试：模型创建、查询、外键关系

### 5.2 前端测试

- [ ] Widget 测试：核心页面渲染
- [ ] 单元测试：`report.dart` / `model_config.dart` 的 `fromJson`
- [ ] 集成测试：API 客户端 Mock 测试
- [ ] 真机测试清单：
  - [ ] Android 真机录制 + 上传
  - [ ] 音频播放（TTS）
  - [ ] 设置保存 + 连通测试
  - [ ] 大文件上传稳定性

---

## 第六阶段：部署与交付

### 6.1 后端部署

- [ ] 编写 Dockerfile（Python 3.12 + FastAPI）
- [ ] 编写 docker-compose.yml（后端 + SQLite 卷挂载）
- [ ] 添加健康检查接口 `/health`（已有，需完善）
- [ ] 添加日志系统（logging + 文件轮转）
- [ ] 配置 HTTPS（Let's Encrypt 或自签名）

### 6.2 前端打包

- [ ] Android APK 构建（`flutter build apk --release`）
- [ ] iOS 构建（需要 macOS + Xcode）
- [ ] App 图标 + 启动页设计
- [ ] App 签名配置

### 6.3 比赛交付物

- [ ] PPT Demo 视频录制
- [ ] 项目文档完善（README 更新、部署指南）
- [ ] 系统架构 diagrams
- [ ] 比赛答辩准备材料

---

## 推荐执行顺序

```
第一阶段（1-2 天）  ← 当前应从这里开始
  ├── 修复后端 Bug（半天）
  ├── 修复前端 Bug（半天）
  └── 写入 Android 权限（1h）

第二阶段（2-3 天）
  ├── 用户鉴权（1 天）
  ├── 文件管理（半天）
  └── 评估链路完善（1 天）

第三阶段（7-10 天）  ← 工作量最大
  ├── 手型检测接入（2-3 天）
  ├── 音频转录接入（5-7 天）
  └── 曲谱识别接入（3-5 天）

第四阶段（3-5 天）
  ├── 用户体验提升（2 天）
  ├── 数据可视化（2 天）
  └── 数字人升级（1 天）

第五阶段（2-3 天）
  ├── 后端测试（2 天）
  └── 前端测试 + 真机验证（1 天）

第六阶段（1-2 天）
  ├── Docker 部署（半天）
  ├── APK 打包（半天）
  └── 比赛材料准备（1 天）
```

**预估总工期：16-25 天**（根据 AI 模型接入难度浮动）

---

## 技术债务清单

| 类别 | 内容 | 影响 |
|------|------|------|
| CORS | `allow_origins=["*"]` + credentials | 浏览器可能拒绝跨域请求 |
| SQLAlchemy | `declarative_base()` 已弃用 | 未来版本可能移除 |
| datetime | `datetime.utcnow` 已弃用 | Python 3.12+ 警告 |
| Flutter | `withOpacity()` 已弃用 | Flutter 3.27+ 警告 |
| Pydantic | 定义了 schema 但 API 未强制使用 | 响应格式无保证 |
| 字体 | PingFang SC 未打包 | Android 显示不一致 |

---

## 环境规范提醒

- **后端开发**：始终使用 `backend/.venv`（Python 3.12.9）
- **AI 模型**：使用 `backend/.venv-models`（安装 PyTorch 等重型依赖时创建）
- **前端**：Flutter 3.19+，`flutter pub get` 后使用
- **每次会话启动**：先激活虚拟环境，再执行任何 Python 命令
