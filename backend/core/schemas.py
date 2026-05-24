"""Pydantic 数据模型 - 接口请求 / 响应的契约。"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    provider: str = "deepseek"
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.8
    max_tokens: int = 200


class TTSConfig(BaseModel):
    engine: str = "edge-tts"
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"


class PromptConfig(BaseModel):
    system: str
    user_template: str


class ThresholdConfig(BaseModel):
    silence_seconds: float = 3.0
    finger_angle_min: int = 90


class FullConfig(BaseModel):
    llm: LLMConfig
    tts: TTSConfig
    prompt: PromptConfig
    thresholds: ThresholdConfig


class ConfigPatch(BaseModel):
    """前端只传想改的字段,其它保持不变。"""
    llm: dict[str, Any] | None = None
    tts: dict[str, Any] | None = None
    prompt: dict[str, Any] | None = None
    thresholds: dict[str, Any] | None = None


class ScoreUploadResponse(BaseModel):
    status: str
    score_id: str
    midi_url: str
    measure_count: int


class HandIssue(BaseModel):
    timestamp: float
    measure: int
    issue_type: str
    description: str


class AudioIssue(BaseModel):
    timestamp: float
    measure: int
    issue_type: str  # wrong_note / missing_note / extra_note
    expected: str | None = None
    actual: str | None = None


class PracticeReport(BaseModel):
    overall_score: int
    rhythm_score: int
    accuracy_score: int
    fluency_score: int
    hand_health_score: int
    wrong_notes: int
    missing_notes: int
    hand_issues_count: int
    teacher_comment: str
    hand_issues: list[HandIssue]
    audio_issues: list[AudioIssue]
    duration_seconds: float


class EvaluateResponse(BaseModel):
    status: str
    report_id: str
    report: PracticeReport
    audio_url: str
