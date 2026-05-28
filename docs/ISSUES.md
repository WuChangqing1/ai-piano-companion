# 问题记录

> 记录开发中遇到的 bug、坑、注意事项

---

### 2026-05-25 Flutter Web 编译失败：camera 包不支持 Web

**问题**：`flutter build web` 编译失败，报错 `CameraPreview` 未定义、`availableCameras()` 未找到。
**原因**：`package:camera` 和 `package:permission_handler` 不支持 Web 平台，直接在 practice_screen.dart 中导入会导致 Web 编译失败。
**解决**：使用 Dart 条件导入（conditional imports）架构：
- `recorder.dart`：抽象接口 + `if (dart.library.html)` / `if (dart.library.io)` 分支
- `recorder_mobile.dart`：使用 `CameraController` + `Permission.camera`
- `recorder_web.dart`：Mock 实现，无 camera 依赖
- `recorder_stub.dart`：默认抛出 `UnsupportedError`
**注意**：`practice_screen.dart` 不能直接 import `camera`，只能 import `recorder.dart`。

### 2026-05-25 端口冲突：8000 / 3000 被占用

**问题**：后端 `main.py` 启动报错 `[Errno 10048]`，Flutter Web 报错 `Failed to bind web development server`。
**原因**：上次进程未正确退出，端口仍被占用。
**解决**：`powershell Get-NetTCPConnection -LocalPort <port> | Stop-Process`，然后重启。
**备选端口**：Flutter Web 可用 5000。

### 2026-05-25 分支管理：当前在 master 而非 develop

**问题**：CLAUDE.md 规定日常开发在 `develop` 分支，但当前在 `master` 分支工作，且 master 领先 origin/master 1 个 commit。
**影响**：不符合项目分支策略，后续 PR 流程会混乱。
**待办**：将 master 上的新 commit 合并到 develop，切回 develop 继续开发。

---

### 2026-05-25 pip 安装 GBK 编码错误

**问题**：`pip install` 时报 `UnicodeDecodeError: 'gbk' codec`。
**原因**：Python 包注释含中文，Windows 默认 GBK 编码无法解析。
**解决**：设置 `set PYTHONUTF8=1` 后重试。

---

### 2026-05-28 ONNX GPU 不可用：cuDNN 缺失

**问题**：RTX 5070 已安装 CUDA 12.9，ONNX Runtime 检测到 CUDAExecutionProvider 但推理仍走 CPU。
**原因**：`onnxruntime-gpu` 需要 cuDNN 9.x DLL（`cudnn64_9.dll`），系统未安装。
**解决**：`pip install nvidia-cudnn-cu12`（安装 cuDNN 9.22），并在 Python 脚本中通过 `os.add_dll_directory()` 注册 `site-packages/nvidia/cudnn/bin/` 路径。

### 2026-05-28 手写 MIDI 生成格式损坏

**问题**：手动拼接 MIDI 二进制时，pretty_midi/Mido 报错 "data byte must be in range 0..127"。
**原因**：1) 手写 variable-length delta encoding 实现有 bug；2) MusicXML 中某些音符音高超出 MIDI 范围（0-127）。
**解决**：改用 `pretty_midi` 库的 Instrument/Note API 构建 MIDI，不再手写 binary。同时 clamp 音高值到 0-127。

### 2026-05-28 conda run 管道 GBK 编码错误

**问题**：`conda run -n AIqinban python script.py` 报 `UnicodeEncodeError: 'gbk'`，conda 管道输出中文时失败。
**原因**：Windows 下 conda run 用 GBK 编码捕获子进程输出，中文/emoji 字符无法编码。
**解决**：改用 Python 解释器完整路径直接运行：`D:/path/to/python.exe script.py`，并设置 `PYTHONIOENCODING=utf-8`。

---

### 2026-05-28 严重 Bug：MusicXML→MIDI 转换遗漏真实速度（tempo）

**问题**：test3 的音频比对报出 105.9 vs 192.5 BPM 的巨大速度差异（86.6 BPM），导致比对完全错误。
**原因**：MusicXML 中 `<sound tempo="90"/>` 标签记录了真实速度，但 `omr_parser.py` 的 MusicXML→MIDI 转换硬编码了 `start_time = beat * 0.5`（即 120 BPM），忽略了 MusicXML 中的实际 tempo 值。
**影响**：所有含有非 120 BPM 曲谱的测试都会得到错误的 MIDI 标准答案，进而导致音频比对结果失真。test3 曲谱实际速度为 90 BPM，但生成的 MIDI 使用 120 BPM，节奏偏移持续累积。
**解决**：在 `run_full_pipeline.py` 中添加 `_read_musicxml_tempo()` 函数，从 MusicXML 的 `<sound tempo="X"/>` 标签读取实际 BPM，并用 `beat_duration = 60.0 / tempo` 正确计算音符时间。需要同步更新 `omr_parser.py` 中的同样逻辑。
**待办**：将 tempo 读取逻辑回迁到 `omr_parser.py` 的生产代码中（当前仅在测试脚本中修复）。

---

### 2026-05-28 MusicXML→MIDI 未使用 divisions 元素做精确时序

**问题**：当前 MusicXML→MIDI 转换使用简化的 note type（eighth/quarter/half）映射时长，未读取 MusicXML 的 `<divisions>` 和 `<duration>` 元素。
**影响**：对于包含附点、三连音、切分音等复杂节奏的曲谱，MIDI 时序不够精确。
**严重程度**：中 — 对大多数简单钢琴谱影响较小，但限制了精度上限。
**状态**：已知问题，待后续优化。

---

### 2026-05-28 basic-pitch emoji 打印 GBK 编码错误

**问题**：basic-pitch 转录完成后打印日志时包含 emoji（💅），Windows GBK 编码无法处理，报 `UnicodeEncodeError`。
**影响**：仅影响日志输出，MIDI 文件在此之前已成功写入磁盘，实际转录结果不受影响。
**严重程度**：低（纯显示问题）。

---

### 2026-05-28 Oemer "index out of bounds" 警告

**问题**：Oemer 处理某些尺寸的图片时报 "index 2436 is out of bounds"，多次出现。
**影响**：警告不影响最终输出，MusicXML 文件仍然成功生成。
**原因**：Oemer 内部对特定图片尺寸的处理逻辑有边界条件 bug。
**严重程度**：低（非致命警告，输出文件有效）。

---

### 2026-05-28 报告 `skipped_by_filter` 显示为 dict repr

**问题**：HTML/Markdown 报告中 `skipped_by_filter` 字段显示为 `{'手指未张开(span=0.7%)': 1}` 而非格式化的文本。
**原因**：`hand_analysis_data.json` 中该字段存储了原始 Python dict 的字符串表示。
**严重程度**：低（显示格式问题，不影响数据正确性）。
