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
