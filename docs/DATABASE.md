# AI 琴伴 - 数据库设计文档

## 选型

- **DBMS**:SQLite 3(本地文件 `backend/ai_qinban.db`,无需运维)
- **ORM**:SQLAlchemy 2.x
- **建表**:服务启动时由 `db.database.init_db()` 自动创建,无需手动迁移
- 后续上量可平迁 PostgreSQL,只需改 `SQLALCHEMY_DATABASE_URL`

## ER 关系

```
users (1) ────< (N) practice_reports
scores (1) ────< (N) practice_reports
```

## 表结构

### 1. users(用户表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| phone | VARCHAR(20) | UNIQUE, NULLABLE | 手机号(家长端用) |
| open_id | VARCHAR(64) | UNIQUE, NULLABLE | 微信 OpenID |
| nickname | VARCHAR(64) | DEFAULT '琴童' | 昵称 |
| role | VARCHAR(16) | DEFAULT 'child' | child / parent |
| created_at | DATETIME | DEFAULT now | 创建时间 |

### 2. scores(曲谱表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| score_uid | VARCHAR(36) | UNIQUE, INDEX | 对外暴露的 UUID |
| title | VARCHAR(128) | DEFAULT '未命名曲目' | 曲名 |
| midi_path | VARCHAR(256) | | 解析后的标准 MIDI 路径 |
| measure_count | INTEGER | DEFAULT 0 | 小节数 |
| uploaded_by | INTEGER | FK→users.id, NULLABLE | 上传者 |
| created_at | DATETIME | DEFAULT now | |

### 3. practice_reports(练习报告表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 主键 |
| report_uid | VARCHAR(36) | UNIQUE, INDEX | 对外 UUID |
| user_id | INTEGER | FK→users.id, NULLABLE | |
| score_id | INTEGER | FK→scores.id, NULLABLE | |
| overall_score | INTEGER | | 综合分(0-100) |
| rhythm_score | INTEGER | | 节奏 |
| accuracy_score | INTEGER | | 音准 |
| fluency_score | INTEGER | | 流畅度 |
| hand_health_score | INTEGER | | 手型健康度 |
| wrong_notes | INTEGER | DEFAULT 0 | 错音数量 |
| missing_notes | INTEGER | DEFAULT 0 | 漏音数量 |
| hand_issues_count | INTEGER | DEFAULT 0 | 手型异常次数 |
| duration_seconds | FLOAT | DEFAULT 0 | 练习时长 |
| teacher_comment | TEXT | | 数字人评语 |
| raw_json | TEXT | | 完整结构化报告(便于回放/前端二次渲染) |
| audio_path | VARCHAR(256) | | TTS 音频文件路径 |
| created_at | DATETIME | DEFAULT now | |

## 索引策略

- `users.phone`、`users.open_id`、`scores.score_uid`、`practice_reports.report_uid` 均建唯一索引。
- 后续大量查询「某用户最近练习」时,可加复合索引 `(user_id, created_at DESC)`。

## 文件存储约定

- 曲谱原图:`backend/uploads/scores/<uuid>.<ext>`
- 练习视频:`backend/uploads/videos/<uuid>.mp4`
- 解析 MIDI:`backend/static/score_<uuid>.mid`
- TTS 音频:`backend/static/tts_<uuid>.mp3`

`static/` 目录通过 `/static/<filename>` HTTP 暴露,供前端直接拉取。
