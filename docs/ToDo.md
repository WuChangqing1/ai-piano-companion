# 下一步操作清单

> 创建时间：2026-05-26

---

## 1. 安装 ffmpeg（音频提取必需）

basic-pitch 需要从视频中提取音频流，系统必须安装 ffmpeg。

```bash
# 方式一（推荐）：Conda 安装
conda install -n AIqinban ffmpeg -c conda-forge

# 方式二：官网下载后手动加入 PATH
# https://ffmpeg.org/download.html
```

验证：
```bash
conda run -n AIqinban ffmpeg -version
```

---

## 2. 准备测试素材

需要一个**弹钢琴的视频**（mp4 格式）和一个**曲谱图片**（png/jpg/pdf）来跑通全链路：

- **测试视频**：手机后置摄像头录制一段弹钢琴，放到 `backend/test_data/` 目录
- **测试曲谱**：视频对应曲目的曲谱照片，放到 `backend/test_data/` 目录

> 没有的话可以先用任意 mp4 视频 + 任意带五线谱的图片跑跑看，Mock 兜底会生效

---

## 3. 启动后端

```bash
conda activate AIqinban
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

验证：
- 打开浏览器 `http://localhost:8000/docs` → 看到 Swagger API 文档 → 后端正常
- `GET /api/config` → 返回当前配置

---

## 4. 逐模块测试

### 4.1 手型检测（MediaPipe Hands）

```bash
conda run -n AIqinban --cwd backend python -c "
from ai_models.hand_tracker import detect_hand_issues
from pathlib import Path
issues = detect_hand_issues(Path('test_data/你的测试视频.mp4'))
print(f'检测到 {len(issues)} 个手型问题:')
for i in issues: print(f'  {i[\"measure\"]}小节 {i[\"description\"]}')
"
```

### 4.2 音频转录（basic-pitch）

```bash
conda run -n AIqinban --cwd backend python -c "
from ai_models.audio_amt import transcribe_and_diff
from pathlib import Path
result = transcribe_and_diff(Path('test_data/你的测试视频.mp4'))
print(f'转录音符数: {len(result)} 个, 节奏评分: {result[\"rhythm_score\"]}')
"
```

### 4.3 曲谱解析（Oemer）

```bash
conda run -n AIqinban --cwd backend python -c "
from ai_models.omr_parser import parse_score
from pathlib import Path
result = parse_score(Path('test_data/你的曲谱图片.png'))
print(result)
"
```

---

## 5. 全链路端到端测试（Swagger）

1. 浏览器打开 `http://localhost:8000/docs`
2. 调用 `POST /api/evaluate` 上传测试视频
3. 查看返回的 JSON：是否包含 `teacher_comment`、`hand_issues`、`audio_issues`、`audio_url`
4. 验证 TTS 语音：访问返回的 `audio_url`

---

## 6. 启动 Flutter 前端

```bash
cd frontend_app
flutter run -d chrome --web-port 3000
```

浏览器打开 `http://localhost:3000`，体验完整交互流程。

---

## 7. CosyVoice（可选，后续）

```bash
# 创建独立环境
conda create -n AIqinban-models python=3.11 -y

# 安装 CosyVoice（参考官方文档）
# https://github.com/FunAudioLLM/CosyVoice

# 在后端配置中切换 TTS 引擎为 cosyvoice
# 编辑 backend/config.json → tts.engine: "cosyvoice"
```

---

## 注意事项

- **Mock 兜底**：所有 AI 模块在真实模型失败时会自动回退 Mock，不会阻塞整条链路
- **Oemer 首次运行**：首次调用会自动下载预训练模型 checkpoint（约 5-10 分钟）
- **basic-pitch**：走 ONNX 后端，不会安装 TensorFlow，保持环境轻量
