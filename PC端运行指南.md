# 在 PC 端运行 AI 琴伴 App

## 方式一：Flutter Web（推荐用于 Demo 视频）

**优点**：直接在浏览器中运行，方便录屏  
**缺点**：摄像头功能受限（Web 模式下 camera 包可能不工作）

### 步骤

```powershell
cd frontend_app

# 1. 启用 Web 支持
flutter config --enable-web

# 2. 获取依赖
flutter pub get

# 3. 在 Chrome 中运行
flutter run -d chrome
```

### 注意事项

- Web 模式下摄像头录制功能可能无法正常工作
- 建议在 Demo 视频中跳过录制环节，或使用预录视频
- 可以手动调用 API 模拟数据展示反馈页效果

---

## 方式二：Windows 桌面应用

**优点**：原生桌面体验，性能好  
**缺点**：需要 Windows 桌面支持，摄像头功能受限

### 步骤

```powershell
cd frontend_app

# 1. 启用 Windows 桌面支持
flutter config --enable-windows-desktop

# 2. 生成 Windows 平台文件
flutter create . --platforms=windows

# 3. 获取依赖
flutter pub get

# 4. 运行
flutter run -d windows
```

---

## 方式三：Android 模拟器（完整功能）

**优点**：完整功能，包括摄像头  
**缺点**：需要安装 Android Studio，性能可能较慢

### 前置要求

1. 安装 [Android Studio](https://developer.android.com/studio)
2. 创建 Android 虚拟设备（AVD）
3. 建议使用 Android 12+ (API 31+) 镜像

### 步骤

```powershell
cd frontend_app

# 1. 生成 Android 平台文件
flutter create .

# 2. 获取依赖
flutter pub get

# 3. 启动 Android 模拟器
# （在 Android Studio 中启动 AVD）

# 4. 运行
flutter run
```

### 配置 Android 权限

编辑 `android/app/src/main/AndroidManifest.xml`，在 `<manifest>` 标签内添加：

```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.CAMERA"/>
<uses-permission android:name="android.permission.RECORD_AUDIO"/>
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>
<uses-permission android:name="android.permission.READ_MEDIA_VIDEO"/>
```

在 `<application>` 标签内添加：

```xml
android:usesCleartextTraffic="true"
```

---

## 启动后端服务

无论使用哪种方式，都需要先启动后端：

```powershell
# 激活虚拟环境
backend\.venv\Scripts\activate

# 启动后端
python backend\main.py
```

后端启动后访问 `http://localhost:8000/docs` 查看 API 文档。

---

## 配置 App 连接后端

1. 启动 App 后，点击右上角设置按钮
2. 修改「后端 Base URL」：
   - Web/Desktop 模式：`http://localhost:8000`
   - Android 模拟器：`http://10.0.2.2:8000`
3. 点击保存

---

## Demo 视频拍摄建议

### 方案 A：使用 Flutter Web + Mock 数据

1. 运行 Web 版本：`flutter run -d chrome`
2. 调整浏览器窗口为手机比例（按 F12 开发者工具）
3. 录制首页、设置页、反馈页等不需要摄像头的画面
4. 反馈页可以通过直接调用 API 生成 Mock 报告：

```bash
curl -X POST http://localhost:8000/api/evaluate \
  -F "file=@sample.mp4" \
  -F "score_id=test"
```

### 方案 B：使用 Android 模拟器 + 虚拟摄像头

1. 安装 OBS Studio 或其他虚拟摄像头软件
2. 在 Android 模拟器中配置虚拟摄像头
3. 播放预录的钢琴弹奏视频作为摄像头输入
4. 完整录制整个流程

### 方案 C：手机录制 + 投屏（推荐）

1. 在真实 Android 手机上运行 App
2. 使用手机投屏工具（如 scrcpy、Vysor）
3. 在电脑上录制投屏画面
4. 这是最真实、效果最好的方案

---

## 快速测试命令

```powershell
# 测试后端是否启动
curl http://localhost:8000/health

# 测试 LLM 连通性
curl -X POST http://localhost:8000/api/config/test

# 获取配置
curl http://localhost:8000/api/config

# 查看历史报告
curl http://localhost:8000/api/reports
```

---

## 常见问题

### Q: Flutter Web 运行时报错 "camera plugin not supported"
**A**: Web 模式不支持 camera 包，建议使用 Android 模拟器或真机。

### Q: Android 模拟器无法连接后端
**A**: 模拟器中使用 `10.0.2.2` 代替 `localhost`，即 `http://10.0.2.2:8000`。

### Q: 上传文件失败
**A**: 检查后端是否正确启动，以及 CORS 配置是否允许前端域名。

### Q: 录制页黑屏
**A**: 确保已授予摄像头和麦克风权限，检查设备是否有可用摄像头。

---

## 推荐工作流（用于 Demo 视频）

1. **启动后端**：`backend\.venv\Scripts\activate && python backend\main.py`
2. **启动 App**：`flutter run -d chrome`（Web）或真机
3. **展示首页**：渐变背景 + 欢迎语
4. **上传曲谱**：展示曲谱卡片变化
5. **进入录制页**：展示 3-2-1 倒计时
6. **录制过程**：展示计时器 + 脉冲动画
7. **停止录制**：展示波形加载动画
8. **反馈页（高潮）**：圆环评分 + 雷达图 + 打字机评语
9. **返回首页**：展示历史报告列表
