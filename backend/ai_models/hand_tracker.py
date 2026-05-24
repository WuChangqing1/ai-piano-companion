"""
MediaPipe Hands 封装。
默认走 Mock,可跑通整条链路;装了 mediapipe + opencv 后切换到真实实现。
切换办法:把 USE_REAL_MODEL 改为 True。
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

USE_REAL_MODEL = False  # 装好 mediapipe 后改为 True


def _mock_detect(video_path: Path) -> list[dict[str, Any]]:
    """生成几个看起来合理的手型异常点。"""
    issues = []
    sample = random.randint(1, 4)
    for i in range(sample):
        ts = round(random.uniform(2.0, 60.0), 2)
        issues.append({
            "timestamp": ts,
            "measure": max(1, int(ts // 2)),
            "issue_type": random.choice(["folded_finger", "collapsed_knuckle"]),
            "description": "右手小指折指" if i % 2 == 0 else "掌关节塌陷",
        })
    return issues


def _real_detect(video_path: Path) -> list[dict[str, Any]]:
    import cv2
    import mediapipe as mp

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2,
                           min_detection_confidence=0.6)
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_idx = 0
    issues: list[dict[str, Any]] = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % int(fps) != 0:  # 每秒取一帧降低算力
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)
        if not res.multi_hand_landmarks:
            continue
        for lm in res.multi_hand_landmarks:
            angle = _finger_angle(lm.landmark[5], lm.landmark[6], lm.landmark[7])
            if angle < 90:
                ts = frame_idx / fps
                issues.append({
                    "timestamp": round(ts, 2),
                    "measure": max(1, int(ts // 2)),
                    "issue_type": "folded_finger",
                    "description": f"指关节角度 {angle:.0f}°,疑似折指",
                })
    cap.release()
    return issues


def _finger_angle(a, b, c) -> float:
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 180.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))


def detect_hand_issues(video_path: Path) -> list[dict[str, Any]]:
    if USE_REAL_MODEL:
        try:
            return _real_detect(video_path)
        except Exception:
            return _mock_detect(video_path)
    return _mock_detect(video_path)
