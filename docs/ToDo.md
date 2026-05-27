# 下一步操作清单

> 最后更新：2026-05-27

## 已就绪

- [x] **ffmpeg** — 已安装（v8.1.1），Conda 环境可调用
- [x] **测试素材** — 已放入 `backend/test_data/`（已加入 .gitignore）：
  - `test.mp4` — 弹琴练习视频
  - `1.jpg` `2.jpg` `3.jpg` — 曲谱（3 页，按顺序）
- [x] **Conda 环境** — `AIqinban`（Python 3.11），全部依赖已安装

---

## 1. 启动后端

```bash
conda activate AIqinban
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

验证：打开 `http://localhost:8000/docs` 看到 Swagger API 文档。

---

## 2. 逐模块测试（一键运行）

```bash
conda run -n AIqinban --cwd backend python tests/test_models.py
```

测试脚本位于 `backend/tests/test_models.py`，依次执行：
- 手型检测（MediaPipe Hands）
- 音频转录（basic-pitch）
- 曲谱解析（Oemer，逐页）

> 首次运行 Oemer 会自动下载模型 checkpoint（约 5-10 分钟）

---

## 3. 全链路端到端测试（Swagger）

1. 浏览器打开 `http://localhost:8000/docs`
2. 调用 `POST /api/evaluate`：
   - `file`: 选择 `backend/test_data/test.mp4`
   - `score_id`: 先通过 `POST /api/scores` 上传曲谱获取
3. 查看返回 JSON：是否包含 `teacher_comment`、`hand_issues`、`audio_url`
4. 访问 `audio_url` 验证 TTS 语音

---

## 4. 启动 Flutter 前端（可选）

```bash
cd frontend_app
flutter run -d chrome --web-port 3000
```

---

## 5. CosyVoice（可选，后续）

```bash
conda create -n AIqinban-models python=3.11 -y
# 参考 https://github.com/FunAudioLLM/CosyVoice 安装
# 编辑 backend/config.json → tts.engine: "cosyvoice"
```

---

## 注意事项

- **Mock 兜底**：AI 模块异常时自动回退 Mock，不阻塞链路
- **Oemer 首次慢**：首次运行下载 checkpoint ~5-10min，之后秒级
- **basic-pitch**：ONNX 后端，无需 TensorFlow
