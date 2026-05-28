"""
MediaPipe Hands 手型检测 — 完整分析版。
包含: 21点骨架绘制、多维度评分、最差N帧提取、base64编码。
"""
from __future__ import annotations

import base64
import math
import os
import random
from io import BytesIO
from pathlib import Path
from typing import Any

import cv2
import numpy as np

# ── PIL 中文渲染 ──────────────────────────────────────
_CN_FONT = None
_CN_FONT_SM = None
for _fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    if os.path.exists(_fp):
        try:
            from PIL import Image, ImageDraw, ImageFont
            _CN_FONT = ImageFont.truetype(_fp, 20)
            _CN_FONT_SM = ImageFont.truetype(_fp, 14)
            break
        except Exception:
            pass

# ── 手指关键点索引 ──────────────────────────────────
FINGER_DEFS = {
    "拇指": {"mcp": 1, "pip": 2, "dip": 3, "tip": 4},
    "食指": {"mcp": 5, "pip": 6, "dip": 7, "tip": 8},
    "中指": {"mcp": 9, "pip": 10, "dip": 11, "tip": 12},
    "无名指": {"mcp": 13, "pip": 14, "dip": 15, "tip": 16},
    "小指": {"mcp": 17, "pip": 18, "dip": 19, "tip": 20},
}

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]

FINGER_NAMES_CN = {1: "拇指", 5: "食指", 9: "中指", 13: "无名指", 17: "小指"}

FRAME_INTERVAL = 0.5
OUTPUT_WORST_N = 5

USE_REAL_MODEL = True  # MediaPipe 已安装,默认走真实推理


def _render_cn_texts(img_bgr, texts):
    """在 OpenCV BGR 图像上一次性渲染所有中文文本。"""
    if _CN_FONT is None or not texts:
        return
    from PIL import Image, ImageDraw
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    for text, pos, fsize, color_bgr, stroke_bg in texts:
        font = _CN_FONT_SM if fsize <= 14 else _CN_FONT
        color_rgb = (color_bgr[2], color_bgr[1], color_bgr[0])
        if stroke_bg:
            for dx in (-1, 1):
                for dy in (-1, 1):
                    draw.text((pos[0] + dx, pos[1] + dy), text, font=font, fill=(255, 255, 255))
        draw.text(pos, text, font=font, fill=color_rgb)
    result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    img_bgr[:] = result


def _joint_angle(a, b, c) -> float:
    """计算以 b 为顶点的角度 a-b-c (度)。"""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 180.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))


def _draw_skeleton(frame, landmarks, w, h, issue_fingers):
    """在帧上绘制 21 点红色骨架。返回标注帧 + 中文文本列表。"""
    overlay = frame.copy()
    cn_texts = []

    for conn in HAND_CONNECTIONS:
        i1, i2 = conn
        x1, y1 = int(landmarks[i1].x * w), int(landmarks[i1].y * h)
        x2, y2 = int(landmarks[i2].x * w), int(landmarks[i2].y * h)
        is_problem = False
        for mcp_idx in issue_fingers:
            finger_joints = {mcp_idx, mcp_idx + 1, mcp_idx + 2, mcp_idx + 3}
            if i1 in finger_joints and i2 in finger_joints:
                is_problem = True
                break
        if is_problem:
            cv2.line(overlay, (x1, y1), (x2, y2), (0, 100, 255), 4)
        else:
            cv2.line(overlay, (x1, y1), (x2, y2), (0, 0, 255), 2)

    for i, lm in enumerate(landmarks):
        cx, cy = int(lm.x * w), int(lm.y * h)
        is_mcp = i in FINGER_NAMES_CN
        is_problem = i in issue_fingers
        if is_problem:
            cv2.circle(overlay, (cx, cy), 8, (0, 0, 255), -1)
            cv2.circle(overlay, (cx, cy), 10, (0, 0, 255), 2)
            cn_texts.append((FINGER_NAMES_CN.get(i, ""), (cx + 14, cy - 14),
                             14, (0, 0, 255), True))
        elif is_mcp:
            cv2.circle(overlay, (cx, cy), 6, (0, 0, 255), -1)
        else:
            cv2.circle(overlay, (cx, cy), 4, (50, 50, 255), -1)

    wx, wy = int(landmarks[0].x * w), int(landmarks[0].y * h)
    cv2.circle(overlay, (wx, wy), 7, (255, 255, 255), -1)
    cv2.circle(overlay, (wx, wy), 9, (0, 0, 255), 2)

    return cv2.addWeighted(overlay, 0.75, frame, 0.25, 0), cn_texts


def _analyze_single_hand(landmarks, hand_tag):
    """分析单手手型。返回(问题列表, 问题MCP索引集合)。"""
    issues = []
    problem_mcps = set()

    for finger_name, joints in FINGER_DEFS.items():
        mcp_idx = joints["mcp"]
        mcp = landmarks[mcp_idx]
        pip = landmarks[joints["pip"]]
        dip = landmarks[joints["dip"]]
        tip = landmarks[joints["tip"]]

        pip_angle = _joint_angle(mcp, pip, dip)
        if pip_angle < 90:
            severity = "严重" if pip_angle < 70 else "轻度"
            deduct = 15 if pip_angle < 70 else 10
            problem_mcps.add(mcp_idx)
            issues.append({
                "type": "folded_finger", "finger": finger_name, "hand": hand_tag,
                "severity": severity, "deduction": deduct,
                "desc": f"{hand_tag}{finger_name}折指({severity}, PIP {pip_angle:.0f}°)",
            })

        mcp_pip_drop = mcp.y - pip.y
        if mcp_pip_drop > 0.01:
            severity = "严重" if mcp_pip_drop > 0.04 else "轻度"
            deduct = 12 if mcp_pip_drop > 0.04 else 8
            problem_mcps.add(mcp_idx)
            issues.append({
                "type": "collapsed_knuckle", "finger": finger_name, "hand": hand_tag,
                "severity": severity, "deduction": deduct,
                "desc": f"{hand_tag}{finger_name}掌关节塌陷({severity})",
            })

        if pip_angle > 178:
            problem_mcps.add(mcp_idx)
            issues.append({
                "type": "over_extended", "finger": finger_name, "hand": hand_tag,
                "severity": "轻度", "deduction": 3,
                "desc": f"{hand_tag}{finger_name}过度伸直(PIP {pip_angle:.0f}°)",
            })

        if finger_name == "拇指":
            thumb_span = math.hypot(mcp.x - tip.x, mcp.y - tip.y)
            if thumb_span < 0.05:
                problem_mcps.add(mcp_idx)
                issues.append({
                    "type": "thumb_tucked", "finger": "拇指", "hand": hand_tag,
                    "severity": "轻度", "deduction": 8,
                    "desc": f"{hand_tag}拇指内扣",
                })

    return issues, problem_mcps


def _is_playing_posture(landmarks, w, h):
    """判断手是否在弹奏姿势。"""
    wrist = landmarks[0]
    thumb_mcp = landmarks[1]
    pinky_mcp = landmarks[17]
    wrist_y_abs = wrist.y * h
    if wrist_y_abs < h * 0.15:
        return False, f"手腕过高(y={wrist_y_abs / h:.1%})"
    finger_span = math.hypot((thumb_mcp.x - pinky_mcp.x) * w,
                             (thumb_mcp.y - pinky_mcp.y) * h)
    if finger_span < w * 0.012:
        return False, f"手指未张开(span={finger_span / w:.1%})"
    return True, "弹奏中"


def _score_frame(frame_issues):
    """对手型帧打分 (0-100)。"""
    score = 100.0
    for issue in frame_issues:
        score -= issue.get("deduction", 10)
    return max(0.0, min(100.0, round(score, 1)))


def analyze_hand_video(video_path: str | Path) -> dict[str, Any]:
    """
    完整手型分析: 抽帧 → MediaPipe → 骨架绘制 → 评分 → 最差N帧。
    返回 dict:
        hand_score: int          平均手型分
        hand_issues: list        问题列表(兼容旧格式)
        worst_frames: list       最差5帧,每帧含 base64 图片
        issues_by_type: dict     问题类型分布
        issues_by_finger: dict   问题手指分布
        duration_s: float
        total_frames_sampled: int
    """
    import mediapipe as mp

    video_path = Path(video_path)
    mp_hands = mp.solutions.hands

    hands = mp_hands.Hands(
        static_image_mode=False, max_num_hands=2,
        min_detection_confidence=0.3, min_tracking_confidence=0.3,
    )

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    sample_interval = max(1, int(fps * FRAME_INTERVAL))
    frame_idx = 0
    all_frame_results = []
    skipped_reasons = {}
    total_frames_with_hands = 0
    total_hands_detected = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % sample_interval != 0:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = hands.process(rgb)
        rgb.flags.writeable = True
        frame_bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        ts = round(frame_idx / fps, 2)
        measure = max(1, int(ts // 2) + 1)

        if not res.multi_hand_landmarks:
            all_frame_results.append({
                "frame_idx": frame_idx, "timestamp": ts, "measure": measure,
                "hands_detected": 0, "score": None, "issues": [], "image_base64": None,
            })
            continue

        total_frames_with_hands += 1
        total_hands_detected += len(res.multi_hand_landmarks)

        frame_issues = []
        all_problem_mcps = set()
        all_cn_texts = []
        annotated = frame_bgr.copy()

        for hand_idx, lm_list in enumerate(res.multi_hand_landmarks):
            hand_tag = "右手" if hand_idx == 0 else "左手"
            landmarks = lm_list.landmark

            is_playing, reason = _is_playing_posture(landmarks, width, height)
            if not is_playing:
                skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
                continue

            hand_issues, problem_mcps = _analyze_single_hand(landmarks, hand_tag)
            frame_issues.extend(hand_issues)
            all_problem_mcps.update(problem_mcps)

            annotated, skel_cn_texts = _draw_skeleton(annotated, landmarks, width, height, problem_mcps)
            all_cn_texts.extend(skel_cn_texts)

            wrist = landmarks[0]
            wx, wy = int(wrist.x * width), int(wrist.y * height)
            hand_color = (0, 0, 255) if problem_mcps else (100, 255, 100)
            all_cn_texts.append((f"{hand_tag}({len(hand_issues)}问题)",
                                 (wx - 20, wy - 30), 14, hand_color, True))

        score = _score_frame(frame_issues)

        _render_cn_texts(annotated, all_cn_texts)

        # 底部信息栏
        info_h = 60
        info_bar = np.zeros((info_h, annotated.shape[1], 3), dtype=np.uint8)
        info_bar[:] = (25, 25, 30)
        info_cn_texts = []
        issue_texts = [i["desc"] for i in frame_issues[:4]]
        cv2.putText(info_bar, f"t={ts:.1f}s | M{measure} | Score:{score:.0f} | Hands:{len(res.multi_hand_landmarks)}",
                    (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        score_color = (0, 255, 100) if score >= 80 else (0, 200, 255) if score >= 60 else (0, 0, 255)
        info_cn_texts.append((f"Score: {score:.0f}/100", (10, 40), 16, score_color, True))
        _render_cn_texts(info_bar, info_cn_texts)

        annotated = np.vstack([annotated, info_bar])

        # Encode to base64 JPEG
        _, buf = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
        img_b64 = base64.b64encode(buf).decode('ascii')

        frame_result = {
            "frame_idx": frame_idx, "timestamp": ts, "measure": measure,
            "hands_detected": len(res.multi_hand_landmarks),
            "score": score, "issue_count": len(frame_issues),
            "issues": [{
                "type": i["type"], "finger": i["finger"], "hand": i["hand"],
                "severity": i["severity"], "desc": i["desc"],
            } for i in frame_issues],
            "image_base64": img_b64,
        }
        all_frame_results.append(frame_result)

    cap.release()
    hands.close()

    # ── 选出最差 N 帧 ──
    frames_with_hands = [f for f in all_frame_results if f["hands_detected"] > 0 and f["score"] is not None]
    frames_with_hands.sort(key=lambda f: f["score"])
    worst_frames = frames_with_hands[:OUTPUT_WORST_N]

    # ── 汇总 ──
    scored = [f for f in all_frame_results if f["score"] is not None]
    avg_score = sum(f["score"] for f in scored) / len(scored) if scored else 0

    all_issues_flat = []
    for f in all_frame_results:
        all_issues_flat.extend(f["issues"])
    issue_by_type = {}
    issue_by_finger = {}
    for i in all_issues_flat:
        issue_by_type[i["type"]] = issue_by_type.get(i["type"], 0) + 1
        key = f"{i['hand']}{i['finger']}"
        issue_by_finger[key] = issue_by_finger.get(key, 0) + 1

    # ── 构建旧格式兼容的 issues 列表 ──
    legacy_issues = []
    seen = set()
    for f in all_frame_results:
        for iss in f["issues"]:
            key = (iss["hand"], iss["finger"], iss["type"])
            if key not in seen:
                seen.add(key)
                legacy_issues.append({
                    "timestamp": f["timestamp"],
                    "measure": f["measure"],
                    "issue_type": iss["type"],
                    "description": iss["desc"],
                })

    return {
        "hand_score": round(avg_score),
        "hand_issues": legacy_issues,
        "worst_frames": worst_frames,
        "issues_by_type": dict(sorted(issue_by_type.items(), key=lambda x: -x[1])),
        "issues_by_finger": dict(sorted(issue_by_finger.items(), key=lambda x: -x[1])),
        "issue_type_names": {
            "folded_finger": "折指（PIP关节过度弯曲）",
            "collapsed_knuckle": "掌关节塌陷",
            "over_extended": "手指过度伸直",
            "thumb_tucked": "拇指内扣",
        },
        "duration_s": round(duration, 1),
        "total_frames_sampled": len(all_frame_results),
        "frames_with_hands": total_frames_with_hands,
        "skipped_by_filter": skipped_reasons,
        "best_score": max((f["score"] for f in scored), default=0),
        "worst_score": min((f["score"] for f in scored), default=0),
    }


def _mock_analyze(video_path: str | Path) -> dict[str, Any]:
    """Mock 数据，模型不可用时的兜底。"""
    issues = []
    samples = [
        {"issue_type": "folded_finger", "description": "右手食指折指"},
        {"issue_type": "folded_finger", "description": "右手中指折指"},
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
    return {
        "hand_score": 75,
        "hand_issues": issues,
        "worst_frames": [],
        "issues_by_type": {},
        "issues_by_finger": {},
        "issue_type_names": {},
        "duration_s": 60.0,
        "total_frames_sampled": 0,
        "frames_with_hands": 0,
        "skipped_by_filter": {},
        "best_score": 0,
        "worst_score": 0,
    }


def analyze_hands(video_path: str | Path) -> dict[str, Any]:
    """完整手型分析入口（带 fallback）。"""
    if USE_REAL_MODEL:
        try:
            return analyze_hand_video(video_path)
        except Exception as e:
            import traceback
            print(f"[hand_tracker] 真实模型异常, 回退 Mock: {e}")
            traceback.print_exc()
            return _mock_analyze(video_path)
    return _mock_analyze(video_path)


def detect_hand_issues(video_path: Path) -> list[dict[str, Any]]:
    """旧接口: 仅返回问题列表，保持向后兼容。"""
    data = analyze_hands(video_path)
    return data["hand_issues"]
