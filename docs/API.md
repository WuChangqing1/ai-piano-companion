# AI 琴伴 - API 接口文档

> Base URL:`http://<本机局域网IP>:8000`
> 自动生成 OpenAPI:`/docs`(Swagger UI)、`/redoc`

## 通用约定

- 媒体类型:JSON(`application/json`)与 multipart 共存。
- 错误格式:HTTPException 默认 `{"detail": "..."}`。
- 鉴权:MVP 阶段无强制鉴权,业务参数(`user_id`)显式传入。

---

## 1. 健康检查

`GET /health` → `{"ok": true}`

## 2. 用户登录(占位)

`POST /api/auth/login`

```json
{ "phone": "13800000000", "nickname": "小明", "role": "child" }
```

响应:
```json
{ "user_id": 1, "nickname": "小明", "role": "child" }
```

---

## 3. 配置中心(用户自定义模型 API)

### 3.1 读取配置

`GET /api/config?reveal=false`

响应(api_key 默认掩码):
```json
{
  "llm": {
    "provider": "deepseek",
    "base_url": "https://api.deepseek.com/v1",
    "api_key": "****Ab12",
    "model": "deepseek-chat",
    "temperature": 0.8,
    "max_tokens": 200
  },
  "tts": {
    "engine": "edge-tts",
    "voice": "zh-CN-XiaoxiaoNeural",
    "rate": "+0%",
    "pitch": "+0Hz"
  },
  "prompt": {
    "system": "...",
    "user_template": "..."
  },
  "thresholds": { "silence_seconds": 3.0, "finger_angle_min": 90 }
}
```

### 3.2 更新配置(局部 patch)

`POST /api/config`

```json
{
  "llm": {
    "base_url": "https://api.moonshot.cn/v1",
    "api_key": "sk-xxxxx",
    "model": "moonshot-v1-8k"
  },
  "prompt": { "system": "你是一只温柔的小猫老师..." }
}
```

> 规则:
> - `api_key` 为空字符串视作「不修改」。
> - 服务端原子写回 `config.json`,下一次 LLM/TTS 调用立即生效。

### 3.3 连通性测试

`POST /api/config/test` → `{"ok": true, "sample": "你好"}` 或 `{"ok": false, "error": "..."}`

---

## 4. 曲谱上传与解析

`POST /api/upload_score`(multipart/form-data)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | jpg/jpeg/png/pdf |
| title | str | 否 | 默认 "未命名曲目" |

响应:
```json
{
  "status": "success",
  "score_id": "f1a2c3...",
  "midi_url": "/static/score_f1a2c3.mid",
  "measure_count": 24
}
```

---

## 5. 多模态评估(核心)

`POST /api/evaluate`(multipart/form-data)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | mp4/mov 视频 |
| score_id | str | 否 | 关联曲谱 |
| user_id | int | 否 | 关联用户 |

响应:
```json
{
  "status": "success",
  "report_id": "ab12cd...",
  "report": {
    "overall_score": 86,
    "rhythm_score": 90,
    "accuracy_score": 84,
    "fluency_score": 88,
    "hand_health_score": 82,
    "wrong_notes": 2,
    "missing_notes": 1,
    "hand_issues_count": 1,
    "duration_seconds": 58.3,
    "teacher_comment": "宝贝弹得很完整……",
    "hand_issues": [
      {
        "timestamp": 12.5,
        "measure": 6,
        "issue_type": "folded_finger",
        "description": "右手小指折指"
      }
    ],
    "audio_issues": [
      {
        "timestamp": 8.0,
        "measure": 4,
        "issue_type": "wrong_note",
        "expected": "E4",
        "actual": "F4"
      }
    ]
  },
  "audio_url": "http://192.168.1.100:8000/static/tts_xxx.mp3"
}
```

执行链路:
1. 保存视频到 `uploads/videos/`
2. `MediaPipe` 提取手型异常(Mock 兜底)
3. `ByteDance AMT` 转录 + diff(Mock 兜底)
4. `LLM Client`(可配置 API)生成 100 字温和评语
5. `TTS Engine`(edge-tts 默认)合成 `.mp3`
6. 写入 `practice_reports` 表
7. 返回 JSON + 音频 URL

---

## 6. 历史报告

`GET /api/reports?user_id=1&limit=20`

```json
[
  {
    "report_id": "ab12...",
    "created_at": "2026-05-24T12:34:56",
    "overall_score": 86,
    "rhythm_score": 90,
    "accuracy_score": 84,
    "hand_health_score": 82,
    "teacher_comment": "宝贝弹得很完整……"
  }
]
```

`GET /api/reports/{report_id}` 返回完整报告(含 `report.raw_json` 解构后的全字段)。

---

## 7. 静态资源

`GET /static/<filename>` 直接拉取生成的 MIDI / 音频。

---

## 时序图(端到端)

```
App                Backend                LLM API           TTS
 │  POST /evaluate   │                       │                │
 ├──── video ───────▶│                       │                │
 │                   │  hand_tracker         │                │
 │                   │  audio_amt            │                │
 │                   │  → 组装错误 JSON      │                │
 │                   ├──── chat.completion ─▶│                │
 │                   │◀────── teacher_text ──┤                │
 │                   ├──────── synthesize ───────────────────▶│
 │                   │◀─────────── .mp3 ─────────────────────┤
 │                   │  写入 DB              │                │
 │◀──── JSON+audio_url ──┤                  │                │
 │  播放 audio_url                                            │
```
