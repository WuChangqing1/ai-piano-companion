# 变更日志

> 基于 Git 提交历史自动维护

格式基于 [Keep a Changelog](https://keepachangelog.com/)

---

## [Unreleased]

### Added
- [2026-05-25] HTML 交互原型 Demo（`demo/AI琴伴Demo.html`）：手机边框、6页面、数字人动画、雷达图、评分仪表盘
- [2026-05-25] Flutter Web 条件导入架构（`recorder.dart` + `recorder_mobile.dart` + `recorder_web.dart`）
- [2026-05-25] 初始化项目记忆系统（docs/ 目录 + 6 个记忆文件）
- [2026-05-25] 创建 .gitignore（Python / Flutter / IDE / 敏感文件）
- [2026-05-25] 后端 FastAPI 框架（路由、数据库、AI Mock、配置中心）
- [2026-05-25] Flutter 前端框架（页面、组件、API 客户端、设置页）
- [2026-05-25] 项目文档（README / API.md / DATABASE.md）

### Changed
- [2026-05-25] `practice_screen.dart` 全面重写：移除 CameraPreview 直接依赖，添加钢琴键模拟视图 + Mock 数据回退
- [2026-05-25] `home_screen.dart` UI 重设计：渐变头部、曲谱卡片、淡入动画
- [2026-05-25] `feedback_screen.dart` 完整重写：圆环评分、雷达图、打字机评语、问题列表、数字人
- [2026-05-25] `avatar_2d.dart` 重写：齐刘海波波头、眨眼、嘴巴开合、说话发光效果
- [2026-05-25] `app_config.dart` 默认 URL 改为 `http://localhost:8000`
