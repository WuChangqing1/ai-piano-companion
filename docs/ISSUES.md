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

### 2026-05-25 pip 安装 GBK 编码错误

**问题**：`pip install` 时报 `UnicodeDecodeError: 'gbk' codec`。
**原因**：Python 包注释含中文，Windows 默认 GBK 编码无法解析。
**解决**：设置 `set PYTHONUTF8=1` 后重试。
