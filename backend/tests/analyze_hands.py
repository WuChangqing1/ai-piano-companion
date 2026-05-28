"""
手型分析流水线：视频抽帧 → 21点骨架绘制 → 多维度评分 → 最差5帧 → 报告。
用法: conda run -n AIqinban --cwd backend python tests/analyze_hands.py [视频路径]
"""
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

# ── 配置 ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
TEST_DATA = BASE / "test_data"
REPORT_DIR = TEST_DATA / "hand_analysis_report"
DEFAULT_VIDEO = TEST_DATA / "test.mp4"
FRAME_INTERVAL = 0.5  # 每 0.5 秒抽一帧
MAX_FRAMES = 0  # 0 = 不限制, 处理全部
OUTPUT_WORST_N = 5  # 返回最差的 N 张

# ── 手部关键点索引 ──────────────────────────────────
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


def _joint_angle(a, b, c):
    """计算以 b 为顶点的角度 a-b-c (度)."""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 180.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))


def _draw_skeleton(frame, landmarks, w, h, issue_fingers):
    """在帧上绘制 21 点红色骨架。issue_fingers 为有问题的 MCP 索引集合。"""
    overlay = frame.copy()

    # ── 绘制连接线（红色主线 + 问题区域加粗亮黄） ──
    for conn in HAND_CONNECTIONS:
        i1, i2 = conn
        x1, y1 = int(landmarks[i1].x * w), int(landmarks[i1].y * h)
        x2, y2 = int(landmarks[i2].x * w), int(landmarks[i2].y * h)

        # 判断这条线是否属于问题手指
        is_problem = False
        for mcp_idx in issue_fingers:
            # 获取该手指的所有关节索引
            base = mcp_idx
            finger_joints = {base, base + 1, base + 2, base + 3}
            if i1 in finger_joints and i2 in finger_joints:
                is_problem = True
                break

        if is_problem:
            cv2.line(overlay, (x1, y1), (x2, y2), (0, 100, 255), 4)  # 亮橙黄，加粗
        else:
            cv2.line(overlay, (x1, y1), (x2, y2), (0, 0, 255), 2)  # 红色

    # ── 绘制 21 个关键点 ──
    for i, lm in enumerate(landmarks):
        cx, cy = int(lm.x * w), int(lm.y * h)
        is_mcp = i in FINGER_NAMES_CN
        is_problem = i in issue_fingers

        if is_problem:
            # 问题 MCP：大红色圆 + 标签
            cv2.circle(overlay, (cx, cy), 8, (0, 0, 255), -1)
            cv2.circle(overlay, (cx, cy), 10, (0, 0, 255), 2)
            cv2.putText(overlay, FINGER_NAMES_CN.get(i, ""),
                        (cx + 14, cy - 14), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (0, 0, 255), 2)
        elif is_mcp:
            # 正常 MCP：实心红圆
            cv2.circle(overlay, (cx, cy), 6, (0, 0, 255), -1)
        else:
            # 其他关节点（PIP/DIP/TIP）：小红圆
            cv2.circle(overlay, (cx, cy), 4, (50, 50, 255), -1)

    # 手腕点特殊标注
    wx, wy = int(landmarks[0].x * w), int(landmarks[0].y * h)
    cv2.circle(overlay, (wx, wy), 7, (255, 255, 255), -1)
    cv2.circle(overlay, (wx, wy), 9, (0, 0, 255), 2)

    return cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)


def _analyze_single_hand(landmarks, hand_tag):
    """分析单手手型,返回(问题列表, 扣分)。"""
    issues = []
    deductions = 0
    problem_mcps = set()

    for finger_name, joints in FINGER_DEFS.items():
        mcp_idx = joints["mcp"]
        pip_idx = joints["pip"]
        dip_idx = joints["dip"]
        tip_idx = joints["tip"]

        mcp = landmarks[mcp_idx]
        pip = landmarks[pip_idx]
        dip = landmarks[dip_idx]
        tip = landmarks[tip_idx]

        # 1. 折指检测: PIP 关节角度
        pip_angle = _joint_angle(mcp, pip, dip)
        if pip_angle < 90:
            severity = "严重" if pip_angle < 70 else "轻度"
            deduct = 15 if pip_angle < 70 else 10
            deductions += deduct
            problem_mcps.add(mcp_idx)
            issues.append({
                "type": "folded_finger",
                "finger": finger_name,
                "hand": hand_tag,
                "severity": severity,
                "pip_angle": round(pip_angle, 1),
                "deduction": deduct,
                "desc": f"{hand_tag}{finger_name}折指({severity}, PIP {pip_angle:.0f}°)",
            })

        # 2. 掌关节塌陷: MCP 低于 PIP
        mcp_pip_drop = mcp.y - pip.y
        if mcp_pip_drop > 0.01:
            severity = "严重" if mcp_pip_drop > 0.04 else "轻度"
            deduct = 12 if mcp_pip_drop > 0.04 else 8
            deductions += deduct
            problem_mcps.add(mcp_idx)
            issues.append({
                "type": "collapsed_knuckle",
                "finger": finger_name,
                "hand": hand_tag,
                "severity": severity,
                "mcp_pip_drop": round(mcp_pip_drop, 3),
                "deduction": deduct,
                "desc": f"{hand_tag}{finger_name}掌关节塌陷({severity})",
            })

        # 3. 手指过度伸直: PIP 角度 > 178° (几乎完全打直)
        if pip_angle > 178:
            deductions += 3
            problem_mcps.add(mcp_idx)
            issues.append({
                "type": "over_extended",
                "finger": finger_name,
                "hand": hand_tag,
                "severity": "轻度",
                "pip_angle": round(pip_angle, 1),
                "deduction": 3,
                "desc": f"{hand_tag}{finger_name}过度伸直(PIP {pip_angle:.0f}°)",
            })

        # 4. 拇指特殊检测: 拇指是否内扣 (拇指 MCP-TIP 距离过小)
        if finger_name == "拇指":
            thumb_span = math.hypot(mcp.x - tip.x, mcp.y - tip.y)
            if thumb_span < 0.05:
                deductions += 8
                problem_mcps.add(mcp_idx)
                issues.append({
                    "type": "thumb_tucked",
                    "finger": "拇指",
                    "hand": hand_tag,
                    "severity": "轻度",
                    "deduction": 8,
                    "desc": f"{hand_tag}拇指内扣",
                })

    return issues, deductions, problem_mcps


def _score_frame(frame_issues, hands_detected):
    """
    对手型帧打分 (0-100, 越高越好)。
    - 基础分 100
    - 每只手被检测到 +5 (鼓励双手都在)
    - 每个问题扣对应分
    - 最低 0 分
    """
    score = 100.0

    # 扣分
    for issue in frame_issues:
        score -= issue.get("deduction", 10)

    return max(0.0, min(100.0, round(score, 1)))


def analyze_video(video_path: Path, output_dir: Path, frame_interval: float = 0.5):
    """主流程: 分析视频, 返回最差 N 帧和报告数据。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    worst_dir = output_dir / "worst_5"
    worst_dir.mkdir(exist_ok=True)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3,
    )

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"视频: {video_path.name}")
    print(f"  {duration:.1f}s, {total_frames} 帧, {fps:.1f} FPS, {width}x{height}")
    print(f"  抽帧间隔: {frame_interval}s")
    print()

    sample_interval = max(1, int(fps * frame_interval))
    frame_idx = 0
    all_frame_results = []
    total_hands_detected = 0
    total_frames_with_hands = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1

        if frame_idx % sample_interval != 0:
            continue
        if MAX_FRAMES > 0 and len(all_frame_results) >= MAX_FRAMES:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        res = hands.process(rgb)
        rgb.flags.writeable = True
        frame_bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        ts = round(frame_idx / fps, 2)
        measure = max(1, int(ts // 2) + 1)

        if not res.multi_hand_landmarks:
            # 没检测到手, 记录空帧
            all_frame_results.append({
                "frame_idx": frame_idx,
                "timestamp": ts,
                "measure": measure,
                "hands_detected": 0,
                "score": None,
                "issues": [],
                "image_path": None,
            })
            continue

        total_frames_with_hands += 1
        total_hands_detected += len(res.multi_hand_landmarks)

        # ── 分析每只手 ──
        frame_issues = []
        all_problem_mcps = set()
        annotated = frame_bgr.copy()

        for hand_idx, lm_list in enumerate(res.multi_hand_landmarks):
            hand_tag = "右手" if hand_idx == 0 else "左手"
            landmarks = lm_list.landmark

            hand_issues, deductions, problem_mcps = _analyze_single_hand(landmarks, hand_tag)
            frame_issues.extend(hand_issues)
            all_problem_mcps.update(problem_mcps)

            # ── 绘制 21 点红色骨架 ──
            annotated = _draw_skeleton(annotated, landmarks, width, height, problem_mcps)

            # 手标签
            wrist = landmarks[0]
            wx, wy = int(wrist.x * width), int(wrist.y * height)
            hand_color = (0, 0, 255) if problem_mcps else (100, 255, 100)
            cv2.putText(annotated, f"{hand_tag}({len(hand_issues)}问题)",
                        (wx - 20, wy - 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, hand_color, 2)

        # ── 打分 ──
        score = _score_frame(frame_issues, len(res.multi_hand_landmarks))

        # ── 底部信息栏 ──
        info_h = 80
        info_bar = np.zeros((info_h, annotated.shape[1], 3), dtype=np.uint8)
        info_bar[:] = (25, 25, 30)
        issue_texts = [i["desc"] for i in frame_issues[:4]]
        cv2.putText(info_bar, f"t={ts:.1f}s | 小节{measure} | 得分:{score:.0f} | 手数:{len(res.multi_hand_landmarks)}",
                    (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        score_color = (0, 255, 100) if score >= 80 else (0, 200, 255) if score >= 60 else (0, 0, 255)
        cv2.putText(info_bar, f"手型评分: {score:.0f}/100", (10, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, score_color, 2)
        for j, txt in enumerate(issue_texts):
            cv2.putText(info_bar, f"  ! {txt}", (10, 65 + j * 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 150, 255), 1)

        annotated = np.vstack([annotated, info_bar])

        # ── 保存帧 ──
        fname = f"frame_{frame_idx:05d}_t{ts:.1f}s_m{measure}_score{score:.0f}.jpg"
        fpath = frames_dir / fname
        cv2.imwrite(str(fpath), annotated)

        frame_result = {
            "frame_idx": frame_idx,
            "timestamp": ts,
            "measure": measure,
            "hands_detected": len(res.multi_hand_landmarks),
            "score": score,
            "issue_count": len(frame_issues),
            "issues": [{
                "type": i["type"],
                "finger": i["finger"],
                "hand": i["hand"],
                "severity": i["severity"],
                "desc": i["desc"],
            } for i in frame_issues],
            "image_path": str(fpath.relative_to(output_dir)),
        }
        all_frame_results.append(frame_result)

        if frame_issues:
            print(f"  [{len(all_frame_results)}] t={ts:.1f}s 得分={score:.0f} 问题={len(frame_issues)} "
                  f"{issue_texts[0] if issue_texts else ''}")

    cap.release()
    hands.close()

    # ── 选出得分最低的 5 帧 ──
    frames_with_hands = [f for f in all_frame_results if f["hands_detected"] > 0]
    frames_with_hands.sort(key=lambda f: f["score"])

    worst_5 = frames_with_hands[:OUTPUT_WORST_N]

    # 复制最差 5 帧到单独目录
    for rank, wf in enumerate(worst_5, 1):
        src = output_dir / wf["image_path"]
        if src.exists():
            dst = worst_dir / f"worst_{rank:02d}_{Path(wf['image_path']).name}"
            import shutil
            shutil.copy2(str(src), str(dst))
            wf["worst_image_path"] = str(dst.relative_to(output_dir))

    # ── 汇总统计 ──
    scored_frames = [f for f in all_frame_results if f["score"] is not None]
    avg_score = sum(f["score"] for f in scored_frames) / len(scored_frames) if scored_frames else 0
    best_score = max((f["score"] for f in scored_frames), default=0)
    worst_score = min((f["score"] for f in scored_frames), default=0)

    # 问题分布
    all_issues_flat = []
    for f in all_frame_results:
        all_issues_flat.extend(f["issues"])
    issue_by_type = {}
    issue_by_finger = {}
    for i in all_issues_flat:
        issue_by_type[i["type"]] = issue_by_type.get(i["type"], 0) + 1
        key = f"{i['hand']}{i['finger']}"
        issue_by_finger[key] = issue_by_finger.get(key, 0) + 1

    summary = {
        "video": str(video_path.name),
        "duration_s": round(duration, 1),
        "fps": round(fps, 1),
        "resolution": f"{width}x{height}",
        "total_frames_sampled": len(all_frame_results),
        "frames_with_hands": total_frames_with_hands,
        "total_hands_detected": total_hands_detected,
        "avg_score": round(avg_score, 1),
        "best_score": best_score,
        "worst_score": worst_score,
        "total_issues": len(all_issues_flat),
        "issues_by_type": dict(sorted(issue_by_type.items(), key=lambda x: -x[1])),
        "issues_by_finger": dict(sorted(issue_by_finger.items(), key=lambda x: -x[1])),
        "worst_5": worst_5,
    }

    return summary, all_frame_results


def _generate_report(summary: dict, output_dir: Path):
    """生成 Markdown 报告。"""
    lines = [
        "# AI 琴伴 - 手型分析报告",
        "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 分析视频: `{summary['video']}`",
        "",
        "---",
        "",
        "## 一、视频概览",
        "",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 视频时长 | {summary['duration_s']}s |",
        f"| 帧率 | {summary['fps']} FPS |",
        f"| 分辨率 | {summary['resolution']} |",
        f"| 采样帧数 | {summary['total_frames_sampled']} |",
        f"| 检测到手的帧数 | {summary['frames_with_hands']} |",
        f"| 检测到手的总次数 | {summary['total_hands_detected']} |",
        "",
        "---",
        "",
        "## 二、手型综合评分",
        "",
        f"| 指标 | 分数 |",
        f"|------|------|",
        f"| **平均手型分** | **{summary['avg_score']:.0f} / 100** |",
        f"| 最佳帧得分 | {summary['best_score']:.0f} / 100 |",
        f"| 最差帧得分 | {summary['worst_score']:.0f} / 100 |",
        f"| 检测到的问题总数 | {summary['total_issues']} |",
        "",
    ]

    # 评分等级
    if summary['avg_score'] >= 85:
        grade = "优秀 🌟"
        grade_desc = "手型整体规范，继续保持！"
    elif summary['avg_score'] >= 70:
        grade = "良好 👍"
        grade_desc = "手型基本正确，少数手指需要调整。"
    elif summary['avg_score'] >= 55:
        grade = "一般 ⚠️"
        grade_desc = "存在较多手型问题，建议针对性训练。"
    else:
        grade = "需改善 ❗"
        grade_desc = "手型问题较多，请关注下方详细分析。"
    lines += [f"**综合评级: {grade}** — {grade_desc}", ""]

    # 问题分布
    lines += [
        "### 问题类型分布",
        "",
        "| 问题类型 | 次数 | 说明 |",
        "|----------|------|------|",
    ]
    type_desc_map = {
        "folded_finger": "手指折指（PIP关节角度过小）",
        "collapsed_knuckle": "掌关节塌陷（MCP低于PIP）",
        "over_extended": "手指过度伸直（缺乏自然弧度）",
        "thumb_tucked": "拇指内扣",
    }
    for t, c in summary["issues_by_type"].items():
        desc = type_desc_map.get(t, "")
        lines.append(f"| {t} | {c} | {desc} |")

    lines += [
        "",
        "### 问题手指分布",
        "",
        "| 手指 | 问题次数 |",
        "|------|----------|",
    ]
    for f, c in summary["issues_by_finger"].items():
        lines.append(f"| {f} | {c} |")

    # 最差 5 帧详细分析
    lines += [
        "",
        "---",
        "",
        "## 三、手型最差的 5 帧",
        "",
        "> 以下为本次分析中手型问题最严重的 5 个时刻，已按得分从低到高排列。",
        "",
    ]

    for rank, wf in enumerate(summary["worst_5"], 1):
        lines += [
            f"### 第 {rank} 名 — 得分: {wf['score']:.0f} / 100",
            "",
            f"- **时间戳**: {wf['timestamp']}s（第 {wf['measure']} 小节）",
            f"- **检测到手数**: {wf['hands_detected']}",
            f"- **问题数**: {wf['issue_count']}",
            "",
        ]
        if wf["issues"]:
            lines += [
                "| # | 手 | 手指 | 问题类型 | 严重度 |",
                "|---|-----|------|----------|--------|",
            ]
            for i, issue in enumerate(wf["issues"], 1):
                severity_icon = "🔴" if issue["severity"] == "严重" else "🟡"
                lines.append(
                    f"| {i} | {issue['hand']} | {issue['finger']} | "
                    f"{issue['type']} | {severity_icon} {issue['severity']} |"
                )
            lines.append("")

        img_ref = wf.get("worst_image_path", wf.get("image_path", ""))
        if img_ref:
            lines.append(f"![手型帧 {rank}]({img_ref})")
            lines.append("")

    # 建议
    lines += [
        "---",
        "",
        "## 四、练习建议",
        "",
    ]

    # 根据问题类型生成针对性建议
    suggestions = []
    if summary["issues_by_type"].get("folded_finger", 0) > 3:
        suggestions.append(
            "**折指问题突出**：手指第一关节（PIP）过度弯曲。建议每天进行「高抬指」练习——"
            "每根手指单独抬起、垂直落下，保持掌关节支撑。可用硬币放在手背上练习，硬币不掉说明手型稳定。"
        )
    if summary["issues_by_type"].get("collapsed_knuckle", 0) > 3:
        suggestions.append(
            "**掌关节塌陷**：手掌支撑不足。建议练习「握球手型」——"
            "想象手心里握着一个乒乓球，保持手指自然弯曲弧度。弹奏时手腕与前臂保持一条直线。"
        )
    if summary["issues_by_type"].get("over_extended", 0) > 2:
        suggestions.append(
            "**手指过度伸直**：缺乏自然弯曲弧度。弹琴时手指应保持自然弧度（像握鼠标的手型），"
            "避免指关节锁死。可对着镜子慢练，检查手指弧度。"
        )
    if summary["issues_by_type"].get("thumb_tucked", 0) > 0:
        suggestions.append(
            "**拇指内扣**：拇指应保持自然外展，与食指形成 C 形。"
            "练习音阶时特别注意拇指穿越后的位置。"
        )

    if not suggestions:
        suggestions.append("手型整体良好，继续保持当前练习习惯，定期录像自查。")

    for i, s in enumerate(suggestions, 1):
        lines.append(f"{i}. {s}")

    lines += [
        "",
        f"*报告由 AI 琴伴手型分析系统自动生成*",
    ]

    report_path = output_dir / "HAND_ANALYSIS_REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    video_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VIDEO

    if not video_path.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        sys.exit(1)

    print("=" * 60)
    print(" AI 琴伴 - 手型分析流水线")
    print(f" 启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    t0 = time.time()

    # 执行分析
    summary, all_results = analyze_video(video_path, REPORT_DIR, FRAME_INTERVAL)

    # 生成报告
    report_path = _generate_report(summary, REPORT_DIR)

    # 保存 JSON 数据
    json_path = REPORT_DIR / "hand_analysis_data.json"
    json_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f" 分析完成 ({elapsed:.0f}s)")
    print(f"{'=' * 60}")
    print(f"  采样帧数: {summary['total_frames_sampled']}")
    print(f"  检测到手: {summary['frames_with_hands']} 帧")
    print(f"  平均分: {summary['avg_score']:.0f}/100")
    print(f"  总问题数: {summary['total_issues']}")
    print(f"  最差 5 帧已保存到: {REPORT_DIR / 'worst_5'}")
    print(f"  报告: {report_path}")
    print(f"  数据: {json_path}")

    # 展示最差 5 帧
    print(f"\n 手型最差 5 帧:")
    for rank, wf in enumerate(summary["worst_5"], 1):
        issues_str = "; ".join(i["desc"] for i in wf["issues"][:3])
        print(f"  #{rank} t={wf['timestamp']:.1f}s 得分={wf['score']:.0f} | {issues_str}")


if __name__ == "__main__":
    main()
