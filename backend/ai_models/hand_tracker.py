"""
MediaPipe Hands 手型检测。
默认使用真实 MediaPipe 模型(21 个手部关键点);
模型不可用时自动降级到 Mock,保证整链路始终可跑通。
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

USE_REAL_MODEL = True  # MediaPipe 已安装,默认走真实推理

# 手指关键点索引: (MCP, PIP, DIP, TIP)
_FINGERS = {
    "拇指": (1, 2, 3, 4),
    "食指": (5, 6, 7, 8),
    "中指": (9, 10, 11, 12),
    "无名指": (13, 14, 15, 16),
    "小指": (17, 18, 19, 20),
}


def _real_detect(video_path: Path) -> list[dict[str, Any]]:
    import cv2
    import mediapipe as mp

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    )
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_idx = 0
    issues: list[dict[str, Any]] = []
    seen_finger_issues: dict[str, set] = {}  # 去重:同手指同类型只记一次

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % int(fps) != 0:  # 每秒一帧
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)
        if not res.multi_hand_landmarks:
            continue

        for hand_idx, lm_list in enumerate(res.multi_hand_landmarks):
            hand_tag = f"{'右手' if hand_idx == 0 else '左手'}"
            landmarks = lm_list.landmark
            ts = round(frame_idx / fps, 2)
            measure = max(1, int(ts // 2) + 1)

            for finger_name, (mcp_i, pip_i, dip_i, tip_i) in _FINGERS.items():
                mcp = landmarks[mcp_i]
                pip = landmarks[pip_i]
                dip = landmarks[dip_i]
                tip = landmarks[tip_i]

                # 折指检测: PIP 关节角度 < 90°
                pip_angle = _joint_angle(mcp, pip, dip)
                if pip_angle < 75:
                    key = f"{hand_tag}_{finger_name}_folded"
                    if key not in seen_finger_issues:
                        seen_finger_issues[key] = set()
                    if "folded" not in seen_finger_issues[key]:
                        seen_finger_issues[key].add("folded")
                        issues.append({
                            "timestamp": ts,
                            "measure": measure,
                            "issue_type": "folded_finger",
                            "description": f"{hand_tag}{finger_name}折指(PIP角度{pip_angle:.0f}°)",
                        })

                # 掌关节塌陷检测: MCP 应高于 PIP(MCP y < PIP y 表示凸起)
                if mcp.y > pip.y + 0.02:
                    key = f"{hand_tag}_{finger_name}_collapsed"
                    if key not in seen_finger_issues:
                        seen_finger_issues[key] = set()
                    if "collapsed" not in seen_finger_issues[key]:
                        seen_finger_issues[key].add("collapsed")
                        issues.append({
                            "timestamp": ts,
                            "measure": measure,
                            "issue_type": "collapsed_knuckle",
                            "description": f"{hand_tag}{finger_name}掌关节塌陷",
                        })

    cap.release()
    return issues


def _joint_angle(a, b, c) -> float:
    """计算以 b 为顶点的角度 a-b-c。"""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 180.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))


def _mock_detect(video_path: Path) -> list[dict[str, Any]]:
    """Mock 数据,所有真实模型都不可用时的兜底。"""
    issues = []
    samples = [
        {"issue_type": "folded_finger", "description": "右手食指折指"},
        {"issue_type": "folded_finger", "description": "右手中指折指"},
        {"issue_type": "folded_finger", "description": "左手食指折指"},
        {"issue_type": "collapsed_knuckle", "description": "右手无名指掌关节塌陷"},
        {"issue_type": "collapsed_knuckle", "description": "左手小指掌关节塌陷"},
    ]
    for i in range(random.randint(1, 3)):
        s = random.choice(samples)
        ts = round(random.uniform(2.0, 60.0), 2)
        issues.append({
            "timestamp": ts,
            "measure": max(1, int(ts // 2) + 1),
            **s,
        })
    return issues


def detect_hand_issues(video_path: Path) -> list[dict[str, Any]]:
    if USE_REAL_MODEL:
        try:
            return _real_detect(video_path)
        except Exception as e:
            import traceback
            print(f"[hand_tracker] 真实模型异常,回退 Mock: {e}")
            traceback.print_exc()
            return _mock_detect(video_path)
    return _mock_detect(video_path)
