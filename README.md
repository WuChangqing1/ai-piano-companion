# AI 琴伴 — 多模态钢琴陪练 MVP

> 多模态(视觉+音频)钢琴陪练系统。前端 Flutter,后端 FastAPI,局域网部署。
> **核心特点:用户可在 App 设置页自定义 LLM API(支持 DeepSeek / 通义 / 智谱 / Kimi / 本地 Ollama 等所有 OpenAI 兼容服务)与 TTS 引擎。**

## 目录结构

```
ai_qinban_project/
├── backend/        # Python FastAPI
├── frontend_app/   # Flutter
└── docs/
    ├── DATABASE.md  # 数据库设计
    └── API.md       # 接口文档
```

## 一、后端启动

### 1. 环境

- Python 3.10+
- Windows / macOS / Linux 均可

### 2. 安装

```powershell
cd ai_qinban_project\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> MVP 默认使用 Mock 替代真实 MediaPipe/AMT/Oemer,可直接跑通整条链路。
> 接入真实模型时取消 `requirements.txt` 末尾的注释,再装一次。

### 3. 配置 LLM(可选,留空也能跑)

编辑 `backend/config.json`,把 `llm.api_key` 填上你自己的 DeepSeek/通义/Moonshot 等的 key。
**也可以启动后在 App 设置页直接改,改完即时生效。**

### 4. 启动

```powershell
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

浏览器打开 `http://127.0.0.1:8000/docs` 看 Swagger 接口文档。

### 5. 获取本机局域网 IP(给手机端用)

```powershell
ipconfig | findstr IPv4
# 例如 192.168.1.100
```

确认手机和电脑连同一个 Wi-Fi。

## 二、前端启动

### 1. 环境

- Flutter 3.19+
- Android Studio / Xcode 任一(真机调试)

### 2. 初始化

```powershell
cd ai_qinban_project\frontend_app
flutter create .            # 生成 android/ ios/ 等平台目录(只需一次)
flutter pub get
```

### 3. 配置权限

按 `frontend_app/android/app/src/main/AndroidManifest_snippet.txt` 把权限合并到 `AndroidManifest.xml`,iOS 同理修改 `Info.plist`。

### 4. 运行

```powershell
flutter run
```

App 首次启动后:
1. 右上角进入「设置」,把「后端 Base URL」改为后端电脑的局域网 IP,例如 `http://192.168.1.100:8000`。
2. 在「LLM 服务」处选预设(DeepSeek/通义/Kimi/Ollama 等)或手动填,填入 API Key,点「保存全部」。
3. 点「测试 LLM 连通性」验证。

## 三、关键交互流程

1. **主页**:上传曲谱(图片/PDF)→ 显示「当前曲谱」。
2. **录制页**:点「开始练习」→ 后置摄像头全屏 → 弹完点中央大圆「停止」。
3. **加载中**:显示「AI 老师正在思考…」(后端跑链路约 3-10s)。
4. **反馈页**:2D 数字人讲述温和评语 + 完整可视化报告(综合分、4 个维度、音准明细、手型明细)。
5. **历史**:右上角「图表」图标查看历次报告。

## 四、用户自定义模型 API(本项目核心亮点)

| 维度 | 实现方式 |
|------|----------|
| 协议 | OpenAI 兼容 chat.completions(行业事实标准) |
| 可配置 | base_url / api_key / model / temperature / max_tokens / system_prompt / user_template / TTS engine / voice |
| 入口 | App 设置页(`settings_screen.dart`) |
| 同步 | `POST /api/config`,后端原子写回 `config.json`,下一次调用立即生效 |
| 兜底 | 未配 api_key 时自动降级为模板话术,保证整链路始终能跑通 |
| 安全 | 返回时 api_key 默认掩码;前端 obscureText 输入;不进 DB |

## 五、故障排查

| 现象 | 原因 / 处理 |
|------|------------|
| App 提示「读取配置失败」 | 后端 IP 未填对,或后端未启动 |
| 测试 LLM 失败 | api_key / base_url 错;或后端电脑无外网 |
| 录制结束没跳转 | 检查后端日志,大概率视频上传 / 评估接口报错;`receiveTimeout=120s` 已设置 |
| 数字人没声音 | 浏览器/真机要解锁声音权限;或 `audio_url` 在手机端不可达(确认 baseUrl 是局域网 IP 而不是 127.0.0.1) |

## 六、扩展点

- 真实接入:`backend/ai_models/hand_tracker.py` 改 `USE_REAL_MODEL=True`;`audio_amt.py` 接入 ByteDance Piano Transcription;`omr_parser.py` 接 Oemer。
- CosyVoice:`tts_engine.py:_synthesize_cosyvoice` 处填入实现。
- 数字人形象:替换 `lib/widgets/avatar_2d.dart`,可直接换成 `Lottie.asset('assets/avatar/teacher.json')`。
- PPT Demo 短视频导出(P1):用 `screen_recorder` 之类的包在反馈页加录屏导出按钮。
