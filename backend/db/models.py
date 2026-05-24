"""ORM 模型 - 见 docs/DATABASE.md 设计说明。"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    open_id = Column(String(64), unique=True, index=True, nullable=True)  # 微信 openid
    nickname = Column(String(64), default="琴童")
    role = Column(String(16), default="child")  # child / parent
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("PracticeReport", back_populates="user")


class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    score_uid = Column(String(36), unique=True, index=True)
    title = Column(String(128), default="未命名曲目")
    midi_path = Column(String(256))
    measure_count = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PracticeReport(Base):
    __tablename__ = "practice_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uid = Column(String(36), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    score_id = Column(Integer, ForeignKey("scores.id"), nullable=True)

    overall_score = Column(Integer)
    rhythm_score = Column(Integer)
    accuracy_score = Column(Integer)
    fluency_score = Column(Integer)
    hand_health_score = Column(Integer)

    wrong_notes = Column(Integer, default=0)
    missing_notes = Column(Integer, default=0)
    hand_issues_count = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)

    teacher_comment = Column(Text)
    raw_json = Column(Text)  # 完整结构化 JSON
    audio_path = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")
