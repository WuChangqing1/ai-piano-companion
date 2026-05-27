"""
综合评估脚本：对 test_data 中的所有素材进行全面分析，生成详尽报告。
用法: conda run -n AIqinban --cwd backend python tests/run_full_evaluation.py
"""
import json
import os
import subprocess
import sys
import textwrap
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import requests


# ── JSON 序列化增强（处理 numpy 类型） ──────────────
def _json_dumps(obj, **kwargs):
    """支持 numpy 和 Path 类型的 JSON 序列化。"""
    class NumpyEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            if isinstance(o, Path):
                return str(o)
            return super().default(o)
    return json.dumps(obj, cls=NumpyEncoder, **kwargs)

# ── 路径配置 ─────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
TEST_DATA = BASE / "test_data"
REPORT_DIR = TEST_DATA / "evaluation_report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO = TEST_DATA / "test.mp4"
SCORE_IMAGES = [TEST_DATA / f"{i}.jpg" for i in (1, 2, 3)]

# ── DeepSeek API ─────────────────────────────────────
DEEPSEEK_KEY = os.getenv("DeepSeek") or os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_KEY:
    # fallback: read from Windows registry
    import subprocess as _sp
    try:
        for scope in ["User", "Machine"]:
            r = _sp.run(
                ["powershell", "-Command",
                 f"[System.Environment]::GetEnvironmentVariable('DeepSeek', '{scope}')"],
                capture_output=True, text=True
            )
            val = r.stdout.strip()
            if val and val.startswith("sk-"):
                DEEPSEEK_KEY = val
                break
    except Exception:
        pass

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"

# ── 注册 CUDA/cuDNN DLL 路径（确保 ONNX GPU 可用） ──
def _setup_gpu_dlls():
    """确保 CUDA/cuDNN DLL 在 Windows DLL 搜索路径中。"""
    import glob as _glob, site as _site
    dll_dirs = set()
    for sp in _site.getsitepackages():
        for pattern in ["nvidia/cudnn/bin", "nvidia/cublas/bin", "nvidia/cuda_nvrtc/bin"]:
            p = f"{sp}/{pattern}"
            if os.path.isdir(p):
                dll_dirs.add(p)
    for d in dll_dirs:
        try:
            os.add_dll_directory(d)
        except Exception:
            pass
    return dll_dirs

_dll_dirs = _setup_gpu_dlls()
if _dll_dirs:
    print(f"[GPU DLL] 已注册 {len(_dll_dirs)} 个 NVIDIA DLL 目录")


# ── GPU / 设备检测 ───────────────────────────────────
def detect_device():
    """检测可用的计算设备。"""
    info = {"cuda_available": False, "gpu_name": "CPU", "onnx_providers": ["CPUExecutionProvider"]}
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        info["onnx_providers"] = providers
        if "CUDAExecutionProvider" in providers:
            info["cuda_available"] = True
            try:
                info["gpu_name"] = ort.get_device()
            except Exception:
                info["gpu_name"] = "NVIDIA GPU (CUDA)"
    except Exception:
        pass
    return info


DEVICE = detect_device()
print(f"[设备] GPU: {DEVICE['gpu_name']}")
print(f"[设备] ONNX Providers: {DEVICE['onnx_providers']}")


# ═══════════════════════════════════════════════════════
# 1. Oemer 曲谱解析
# ═══════════════════════════════════════════════════════
def _get_oemer_exe():
    """找到 oemer CLI 可执行文件的完整路径。"""
    # 首先在同 conda 环境的 Scripts 目录查找
    import sys
    scripts_dir = Path(sys.prefix) / "Scripts"
    candidates = [
        scripts_dir / "oemer.exe",
        scripts_dir / "oemer",
        Path("D:/App/Business/Coding/Python/Miniconda/envs/AIqinban/Scripts/oemer.exe"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    # 回退到 PATH 搜索
    return "oemer"


def run_oemer_on_all(force_rerun=False):
    """对 3 页曲谱逐页调用 Oemer，输出 MusicXML 并合并为 MIDI。"""
    print("\n" + "=" * 60)
    print(" 阶段 1/4: Oemer 曲谱解析")
    print("=" * 60)

    oemer_exe = _get_oemer_exe()
    print(f"  Oemer CLI: {oemer_exe}")

    results = []
    oemer_dir = REPORT_DIR / "oemer_output"
    oemer_dir.mkdir(parents=True, exist_ok=True)

    for i, img in enumerate(SCORE_IMAGES, 1):
        if not img.exists():
            print(f"  [{i}/3] SKIP: {img.name} not found")
            continue

        page_out = oemer_dir / f"page_{i}"
        page_out.mkdir(parents=True, exist_ok=True)
        mxl_files = list(page_out.glob("*.musicxml")) + list(page_out.glob("*.xml"))

        if mxl_files and not force_rerun:
            print(f"  [{i}/3] 缓存命中 {img.name} → {len(mxl_files)} musicxml, 跳过")
            results.append({
                "page": i, "file": img.name, "status": "OK",
                "elapsed_s": 0,
                "musicxml_count": len(mxl_files),
                "output_dir": str(page_out),
                "stderr_tail": "",
            })
            continue

        print(f"  [{i}/3] 解析 {img.name} ...", flush=True)
        t0 = time.time()

        # 复制到临时 ASCII 路径（Oemer 中文路径兼容）
        import shutil, tempfile
        tmp_dir = Path(tempfile.mkdtemp(prefix="oemer_"))
        tmp_img = tmp_dir / f"score_{i}{img.suffix}"
        shutil.copy2(img, tmp_img)

        try:
            res = subprocess.run(
                [oemer_exe, str(tmp_img), "-o", str(page_out), "--without-deskew"],
                capture_output=True, timeout=600,
            )
            elapsed = time.time() - t0

            mxl_files = list(page_out.glob("*.musicxml")) + list(page_out.glob("*.xml"))
            status = "OK" if res.returncode == 0 and mxl_files else "FAIL"
            print(f"    → {status} ({elapsed:.0f}s), returncode={res.returncode}, "
                  f"musicxml={'yes' if mxl_files else 'no'}")
            if res.returncode != 0:
                stderr_tail = res.stderr.decode("gbk", errors="replace")[-300:]
                print(f"    stderr: ...{stderr_tail}")

            results.append({
                "page": i, "file": img.name, "status": status,
                "elapsed_s": round(elapsed, 1),
                "musicxml_count": len(mxl_files),
                "output_dir": str(page_out),
                "stderr_tail": res.stderr.decode("gbk", errors="replace")[-500:] if res.returncode != 0 else "",
            })
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # 合并所有页的 MusicXML notes 为一个综合 MIDI
    combined_midi = _merge_oemer_to_midi(results, oemer_dir)
    combined_json = REPORT_DIR / "oemer_results.json"
    combined_json.write_text(_json_dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  Oemer 汇总: {len([r for r in results if r['status']=='OK'])}/{len(results)} 页成功")
    if combined_midi:
        print(f"  合并 MIDI: {combined_midi}")
    return results, combined_midi


def _merge_oemer_to_midi(results, oemer_dir):
    """将多页 Oemer MusicXML 合并为一个标准 MIDI 文件（使用 pretty_midi）。"""
    import xml.etree.ElementTree as ET
    import pretty_midi

    NOTE_DURATIONS = {
        "whole": 4.0, "half": 2.0, "quarter": 1.0,
        "eighth": 0.5, "16th": 0.25, "32nd": 0.125,
    }

    pm = pretty_midi.PrettyMIDI(initial_tempo=120)
    piano = pretty_midi.Instrument(program=0, name="Piano")

    measure_offset = 0
    total_measures = 0
    all_note_count = 0

    for r in results:
        if r["status"] != "OK":
            continue
        page_dir = Path(r["output_dir"])
        mxl_files = list(page_dir.glob("*.musicxml")) + list(page_dir.glob("*.xml"))
        if not mxl_files:
            continue

        try:
            tree = ET.parse(str(mxl_files[0]))
            root = tree.getroot()
        except Exception:
            continue

        parts = root.findall("part")
        if not parts:
            parts = [root]

        page_max_measures = 0
        for part in parts:
            measures = part.findall("measure")
            page_max_measures = max(page_max_measures, len(measures))
            tick = 0
            for measure in measures:
                for note in measure.findall("note"):
                    pitch_elem = note.find("pitch")
                    if pitch_elem is None:
                        # 休止符
                        dur_elem = note.find("type")
                        rest_dur = NOTE_DURATIONS.get(dur_elem.text.strip(), 1.0) if dur_elem is not None and dur_elem.text else 1.0
                        tick += rest_dur
                        continue
                    step = (pitch_elem.findtext("step") or "C").strip()
                    octave = int(pitch_elem.findtext("octave") or "4")
                    alter = int(pitch_elem.findtext("alter") or "0")
                    base_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
                    midi_num = max(0, min(127, (octave + 1) * 12 + base_map.get(step.upper(), 0) + alter))

                    dur_elem = note.find("type")
                    dur = NOTE_DURATIONS.get(dur_elem.text.strip(), 1.0) if dur_elem is not None and dur_elem.text else 1.0

                    beat_start = tick + measure_offset * 4
                    start_time = beat_start / 4.0 * 2.0  # 假设 120 BPM, 每拍 0.5s
                    end_time = (beat_start + dur) / 4.0 * 2.0

                    note_obj = pretty_midi.Note(
                        velocity=80, pitch=midi_num,
                        start=start_time, end=end_time
                    )
                    piano.notes.append(note_obj)
                    all_note_count += 1
                    tick += dur

        measure_offset += page_max_measures
        total_measures += page_max_measures

    if all_note_count == 0:
        return None

    pm.instruments.append(piano)

    midi_path = oemer_dir / "combined_score.mid"
    pm.write(str(midi_path))
    print(f"  合并 MIDI: {all_note_count} 个音符, {total_measures} 小节 → {midi_path.name}")
    return midi_path


# ═══════════════════════════════════════════════════════
# 2. 手型检测 + 可视化
# ═══════════════════════════════════════════════════════
import mediapipe as mp

# MediaPipe 手部关键点连接关系（用于绘制骨架）
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # 拇指
    (0, 5), (5, 6), (6, 7), (7, 8),       # 食指
    (0, 9), (9, 10), (10, 11), (11, 12),  # 中指
    (0, 13), (13, 14), (14, 15), (15, 16),# 无名指
    (0, 17), (17, 18), (18, 19), (19, 20),# 小指
    (5, 9), (9, 13), (13, 17),             # 掌部横向
]

FINGER_NAMES = {1: "拇指", 5: "食指", 9: "中指", 13: "无名指", 17: "小指"}

# 手指关键点索引: (MCP, PIP, DIP, TIP)
FINGERS = {
    "拇指": (1, 2, 3, 4),
    "食指": (5, 6, 7, 8),
    "中指": (9, 10, 11, 12),
    "无名指": (13, 14, 15, 16),
    "小指": (17, 18, 19, 20),
}


def _joint_angle(a, b, c):
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = (v1[0]**2 + v1[1]**2) ** 0.5
    n2 = (v2[0]**2 + v2[1]**2) ** 0.5
    if n1 == 0 or n2 == 0:
        return 180.0
    import math
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))


def run_hand_tracking():
    """逐帧分析视频手型，输出标注图片。"""
    print("\n" + "=" * 60)
    print(" 阶段 2/4: 手型检测与可视化")
    print("=" * 60)

    hands_dir = REPORT_DIR / "hand_frames"
    hands_dir.mkdir(parents=True, exist_ok=True)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.3,  # 降低阈值捕获更多手型
        min_tracking_confidence=0.3,
    )

    cap = cv2.VideoCapture(str(VIDEO))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"  视频: {duration:.1f}s, {total_frames} 帧, {fps:.1f} FPS, {width}x{height}")

    all_issues = []
    good_frame_saved = 0
    bad_frame_saved = 0
    max_good = 6  # 最多保留 6 张"好"帧
    max_bad = 20  # 最多保留 20 张"问题"帧

    frame_idx = 0
    sample_interval = max(1, int(fps * 0.5))  # 每 0.5s 抽一帧

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
            continue

        frame_issues = []
        annotated = frame_bgr.copy()
        h, w = annotated.shape[:2]

        for hand_idx, lm_list in enumerate(res.multi_hand_landmarks):
            hand_tag = "右手" if hand_idx == 0 else "左手"
            landmarks = lm_list.landmark

            # ── 手指问题检测 ──
            problem_fingers = set()
            for finger_name, (mcp_i, pip_i, dip_i, tip_i) in FINGERS.items():
                mcp = landmarks[mcp_i]
                pip = landmarks[pip_i]
                dip = landmarks[dip_i]

                # 折指检测（放宽阈值：< 100°）
                pip_angle = _joint_angle(mcp, pip, dip)
                if pip_angle < 100:
                    problem_fingers.add(mcp_i)
                    frame_issues.append({
                        "timestamp": ts, "measure": measure,
                        "hand": hand_tag, "finger": finger_name,
                        "issue_type": "folded_finger",
                        "pip_angle": round(pip_angle, 1),
                        "description": f"{hand_tag}{finger_name}折指(PIP {pip_angle:.0f}°)",
                    })

                # 掌关节塌陷检测（放宽阈值）
                if mcp.y > pip.y + 0.01:
                    problem_fingers.add(mcp_i)
                    frame_issues.append({
                        "timestamp": ts, "measure": measure,
                        "hand": hand_tag, "finger": finger_name,
                        "issue_type": "collapsed_knuckle",
                        "description": f"{hand_tag}{finger_name}掌关节塌陷",
                    })

            # ── 绘制骨架 ──
            all_finger_mcps = [idx for idx in FINGER_NAMES]
            for mcp_idx in all_finger_mcps:
                color = (0, 0, 255) if mcp_idx in problem_fingers else (0, 255, 100)
                thickness = 3 if mcp_idx in problem_fingers else 1
                # 画 MCP 点（手指根部）
                lm = landmarks[mcp_idx]
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(annotated, (cx, cy), 6, color, -1)
                if mcp_idx in problem_fingers:
                    cv2.putText(annotated, FINGER_NAMES.get(mcp_idx, ""),
                                (cx + 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.5, (0, 0, 255), 1)

            # 标准 MediaPipe 骨架绘制（半透明覆盖）
            overlay = annotated.copy()
            mp_draw.draw_landmarks(
                overlay, lm_list, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )
            annotated = cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0)

            # 手标签
            wrist = landmarks[0]
            wx, wy = int(wrist.x * w), int(wrist.y * h)
            cv2.putText(annotated, hand_tag, (wx - 20, wy - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # ── 标注信息栏 ──
        info_bar = np.zeros((60, annotated.shape[1], 3), dtype=np.uint8)
        info_bar[:] = (30, 30, 30)
        cv2.putText(info_bar, f"Time: {ts:.1f}s | Measure: {measure} | Issues: {len(frame_issues)}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        status = "PROBLEM DETECTED" if frame_issues else "HAND POSTURE OK"
        color = (0, 0, 255) if frame_issues else (0, 255, 100)
        cv2.putText(info_bar, status, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        annotated = np.vstack([annotated, info_bar])

        # ── 保存帧 ──
        if frame_issues:
            all_issues.extend(frame_issues)
            if bad_frame_saved < max_bad:
                fname = hands_dir / f"BAD_m{measure}_t{ts:.1f}s_{bad_frame_saved+1:02d}.jpg"
                cv2.imwrite(str(fname), annotated)
                bad_frame_saved += 1
                print(f"    [问题帧] {fname.name}: " + "; ".join(
                    i["description"] for i in frame_issues))
        else:
            if good_frame_saved < max_good:
                fname = hands_dir / f"GOOD_m{measure}_t{ts:.1f}s_{good_frame_saved+1:02d}.jpg"
                cv2.imwrite(str(fname), annotated)
                good_frame_saved += 1
                print(f"    [正常帧] {fname.name}: 手型良好")

    cap.release()
    hands.close()

    # 保存手型问题 JSON
    hand_json = REPORT_DIR / "hand_issues.json"
    hand_json.write_text(_json_dumps({
        "total_issues": len(all_issues),
        "issues_by_type": _group_by(all_issues, "issue_type"),
        "issues_by_finger": _group_by(all_issues, "finger"),
        "issues_detail": all_issues,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  手型汇总: {len(all_issues)} 个问题, "
          f"正常帧 {good_frame_saved} 张, 问题帧 {bad_frame_saved} 张")
    return all_issues, good_frame_saved, bad_frame_saved


def _group_by(items, key):
    result = {}
    for item in items:
        k = item.get(key, "unknown")
        result[k] = result.get(k, 0) + 1
    return dict(sorted(result.items(), key=lambda x: -x[1]))


# ═══════════════════════════════════════════════════════
# 3. 音频转录与分析
# ═══════════════════════════════════════════════════════
def run_audio_analysis(standard_midi=None):
    """basic-pitch 转录音频 + 与标准 MIDI 比对。"""
    print("\n" + "=" * 60)
    print(" 阶段 3/4: 音频转录与比对分析")
    print("=" * 60)

    from basic_pitch.inference import predict
    import pretty_midi

    # 提取音频
    audio_path = VIDEO.with_suffix(".wav")
    if not audio_path.exists() or audio_path.stat().st_size == 0:
        print("  提取音频...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(VIDEO), "-vn", "-acodec", "pcm_s16le",
             "-ar", "22050", "-ac", "1", str(audio_path)],
            capture_output=True,
        )

    print(f"  音频文件: {audio_path} ({audio_path.stat().st_size / 1024:.0f} KB)")

    # basic-pitch 转录
    print("  basic-pitch ONNX 转录中...")
    t0 = time.time()
    _, midi_data, midi_notes = predict(str(audio_path))
    elapsed = time.time() - t0
    print(f"  转录完成 ({elapsed:.0f}s)")

    # 提取转录音符（转换为 Python 原生类型）
    transcribed = []
    for inst in midi_data.instruments:
        for note in inst.notes:
            transcribed.append({
                "pitch": int(note.pitch),
                "start": round(float(note.start), 2),
                "end": round(float(note.end), 2),
                "velocity": int(note.velocity),
            })

    duration = max((n["end"] for n in transcribed), default=0)
    print(f"  转录音符: {len(transcribed)} 个, 时长: {duration:.1f}s")

    # 保存转录 MIDI
    trans_midi_path = REPORT_DIR / "transcribed_audio.mid"
    midi_data.write(str(trans_midi_path))
    print(f"  转录 MIDI: {trans_midi_path}")

    # ── 与标准 MIDI 比对 ──
    standard_notes = []
    if standard_midi and Path(standard_midi).exists():
        print(f"\n  标准 MIDI: {standard_midi} → 加载中...")
        try:
            pm = pretty_midi.PrettyMIDI(str(standard_midi))
            for inst in pm.instruments:
                for note in inst.notes:
                    standard_notes.append({
                        "pitch": int(note.pitch),
                        "start": round(float(note.start), 2),
                        "end": round(float(note.end), 2),
                        "velocity": int(note.velocity),
                    })
            print(f"  标准音符: {len(standard_notes)} 个")
        except Exception as e:
            print(f"  标准 MIDI 加载失败: {e}")

    diff = _detailed_diff(transcribed, standard_notes) if standard_notes else _analyze_without_reference(transcribed)

    # 保存完整结果
    audio_json = REPORT_DIR / "audio_analysis.json"
    audio_json.write_text(_json_dumps({
        "transcribed_count": len(transcribed),
        "standard_count": len(standard_notes),
        "duration_s": round(duration, 1),
        "has_reference": bool(standard_notes),
        "diff": {k: v for k, v in diff.items() if k != "all_notes"},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # 保存详细音符级分析
    notes_detail_path = REPORT_DIR / "audio_note_details.json"
    notes_detail_path.write_text(_json_dumps(diff.get("all_notes", diff), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  音频分析完成:")
    for k, v in diff.items():
        if k != "all_notes":
            print(f"    {k}: {v if isinstance(v, (int, float)) else len(v)}")

    return diff, transcribed, standard_notes


def _detailed_diff(transcribed, standard):
    """详细比对：每个音符的匹配情况。"""
    wrong = []
    missing = []
    extra = []
    matched = []
    all_note_analysis = []

    # 时间对齐后逐个匹配
    std_by_time = {}
    for s in standard:
        t = round(s["start"])
        std_by_time.setdefault(t, []).append(s)

    tra_by_time = {}
    for t in transcribed:
        t_round = round(t["start"])
        tra_by_time.setdefault(t_round, []).append(t)

    # 简单时间窗口匹配 (0.5s 容差)
    used_std = set()
    used_tra = set()

    for i, t_note in enumerate(transcribed):
        t_start = t_note["start"]
        best_match = None
        best_diff = 999

        for j, s_note in enumerate(standard):
            if j in used_std:
                continue
            time_diff = abs(s_note["start"] - t_start)
            pitch_match = (s_note["pitch"] % 12) == (t_note["pitch"] % 12)
            if time_diff < 1.0 and pitch_match and time_diff < best_diff:
                best_diff = time_diff
                best_match = (j, s_note)

        if best_match:
            j, s_note = best_match
            used_std.add(j)
            used_tra.add(i)
            timing_err = abs(t_note["start"] - s_note["start"])
            dur_err = abs((t_note["end"] - t_note["start"]) - (s_note["end"] - s_note["start"]))
            all_note_analysis.append({
                "status": "matched",
                "pitch": _pitch_name(t_note["pitch"]),
                "expected_start": s_note["start"],
                "actual_start": t_note["start"],
                "timing_error_s": round(timing_err, 2),
                "duration_error_s": round(dur_err, 2),
            })
            matched.append({
                "expected": _pitch_name(s_note["pitch"]),
                "actual": _pitch_name(t_note["pitch"]),
                "timing_error": round(timing_err, 2),
            })
        else:
            # 检查是和标准音符时差太大还是完全多余
            close_std = [s for j, s in enumerate(standard) if j not in used_std and abs(s["start"] - t_start) < 1.5]
            if close_std:
                # 时间接近但音高不匹配 = 错音
                s_note = close_std[0]
                all_note_analysis.append({
                    "status": "wrong_note",
                    "pitch_actual": _pitch_name(t_note["pitch"]),
                    "pitch_expected": _pitch_name(s_note["pitch"]),
                    "time_s": t_start,
                })
                wrong.append({
                    "timestamp": round(t_start, 1),
                    "expected": _pitch_name(s_note["pitch"]),
                    "actual": _pitch_name(t_note["pitch"]),
                })
            else:
                all_note_analysis.append({
                    "status": "extra_note",
                    "pitch": _pitch_name(t_note["pitch"]),
                    "time_s": t_start,
                })
                extra.append({
                    "timestamp": round(t_start, 1),
                    "pitch": _pitch_name(t_note["pitch"]),
                })

    # 漏音检测：标准音符中未被匹配的
    for j, s_note in enumerate(standard):
        if j not in used_std:
            all_note_analysis.append({
                "status": "missing_note",
                "pitch": _pitch_name(s_note["pitch"]),
                "expected_time_s": s_note["start"],
            })
            missing.append({
                "timestamp": round(s_note["start"], 1),
                "pitch": _pitch_name(s_note["pitch"]),
            })

    rhythm_score = _calc_rhythm_score(transcribed)
    accuracy = round(len(matched) / max(len(standard), 1) * 100, 1)

    return {
        "accuracy_pct": accuracy,
        "rhythm_score": rhythm_score,
        "matched_count": len(matched),
        "wrong_notes": wrong,
        "missing_notes": missing,
        "extra_notes": extra,
        "all_notes": all_note_analysis,
    }


def _analyze_without_reference(transcribed):
    """无参考谱时的独立分析。"""
    if not transcribed:
        return {"error": "No notes detected"}

    pitches = [n["pitch"] for n in transcribed]
    durations = [n["end"] - n["start"] for n in transcribed]
    iois = []
    sorted_notes = sorted(transcribed, key=lambda n: n["start"])
    for i in range(1, len(sorted_notes)):
        iois.append(sorted_notes[i]["start"] - sorted_notes[i - 1]["start"])

    import statistics
    pitch_range = f"{_pitch_name(min(pitches))} ~ {_pitch_name(max(pitches))}"
    rhythm_score = _calc_rhythm_score(transcribed)

    note_analysis = []
    for i, n in enumerate(sorted_notes):
        note_analysis.append({
            "index": i + 1,
            "pitch": _pitch_name(n["pitch"]),
            "midi_num": n["pitch"],
            "start_s": n["start"],
            "duration_s": round(n["end"] - n["start"], 2),
            "velocity": n["velocity"],
        })

    return {
        "rhythm_score": rhythm_score,
        "note_count": len(transcribed),
        "pitch_range": pitch_range,
        "duration_total_s": round(max((n["end"] for n in transcribed), default=0), 1),
        "avg_duration_s": round(statistics.mean(durations), 2) if durations else 0,
        "tempo_bpm": round(60 / statistics.mean(iois), 1) if iois else 0,
        "rhythm_consistency": "稳定" if rhythm_score >= 80 else "一般" if rhythm_score >= 60 else "不稳定",
        "all_notes": note_analysis,
    }


def _calc_rhythm_score(notes):
    if len(notes) < 3:
        return 85
    import statistics
    sorted_notes = sorted(notes, key=lambda n: n["start"])
    iois = []
    for i in range(1, len(sorted_notes)):
        iois.append(sorted_notes[i]["start"] - sorted_notes[i - 1]["start"])
    try:
        cv = statistics.stdev(iois) / statistics.mean(iois)
    except Exception:
        return 85
    return max(50, min(95, 95 - int(cv * 30)))


def _pitch_name(midi_num):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[midi_num % 12]}{midi_num // 12 - 1}"


# ═══════════════════════════════════════════════════════
# 4. DeepSeek 生成综合评估报告
# ═══════════════════════════════════════════════════════
def generate_ai_report(oemer_results, hand_issues, audio_diff, combined_midi):
    """使用 DeepSeek API 生成中文评估报告。"""
    print("\n" + "=" * 60)
    print(" 阶段 4/4: DeepSeek 生成评估报告")
    print("=" * 60)

    if not DEEPSEEK_KEY:
        print("  [警告] DeepSeek API Key 未找到，将生成基础报告")
        return _generate_basic_report(oemer_results, hand_issues, audio_diff)

    # ── 整理数据 ──
    hand_summary = {
        "total_issues": len(hand_issues),
        "by_type": _group_by(hand_issues, "issue_type"),
        "by_finger": _group_by(hand_issues, "finger"),
        "sample_issues": hand_issues[:15],
    }

    audio_summary = {
        k: v for k, v in audio_diff.items()
        if k in ("accuracy_pct", "rhythm_score", "matched_count",
                  "note_count", "pitch_range", "tempo_bpm", "duration_total_s",
                  "avg_duration_s", "rhythm_consistency")
    }
    audio_issues = {
        "wrong_notes": audio_diff.get("wrong_notes", [])[:10],
        "missing_notes": audio_diff.get("missing_notes", [])[:10],
        "extra_notes": audio_diff.get("extra_notes", [])[:10],
    }

    oemer_summary = {
        "total_pages": len(oemer_results),
        "success_pages": len([r for r in oemer_results if r["status"] == "OK"]),
        "failed_pages": len([r for r in oemer_results if r["status"] != "OK"]),
    }

    # ── 系统 Prompt ──
    system_prompt = textwrap.dedent("""\
    你是一位资深的钢琴教育专家和AI音乐分析系统的评估师。你需要基于提供的客观数据,
    生成一份专业、详尽的中文评估报告。

    报告格式要求:
    1. 使用 Markdown 格式
    2. 每个分析维度都要有"数据呈现"和"专家解读"两部分
    3. 给出具体的练习建议(不是泛泛的"多练",而是针对具体问题的可操作建议)
    4. 评分使用百分制
    5. 语气专业但不冰冷,鼓励学生进步

    报告结构:
    # AI 琴伴 - 综合练习评估报告
    ## 一、总体评分
    ## 二、手型分析 (详细逐项分析)
    ## 三、音准分析 (错音/漏音/多余音详析)
    ## 四、节奏分析
    ## 五、曲谱识别结果
    ## 六、针对性练习建议
    ## 七、下次练习目标
    """)

    # ── 用户 Prompt ──
    hand_issues_text = _json_dumps(hand_summary, ensure_ascii=False, indent=2)
    audio_text = _json_dumps({**audio_summary, **audio_issues}, ensure_ascii=False, indent=2)
    oemer_text = _json_dumps(oemer_summary, ensure_ascii=False, indent=2)

    user_prompt = f"""请根据以下分析数据生成详尽的评估报告。

    ## 手型检测数据
    {hand_issues_text}

    ## 音频分析数据
    {audio_text}

    ## 曲谱解析数据
    {oemer_text}

    要求:
    - 手型部分: 具体到每根手指的问题频率,分析原因(力量不足?姿势不对?紧张?)
    - 音频部分: 逐项分析错音/漏音/多余音,并推测原因(读谱错误?指法问题?节奏不稳?)
    - 节奏部分: 分析节奏稳定性,给出节拍器使用建议
    - 建议部分: 给出3-5条可立即执行的练习建议
    - 报告需包含具体的音名(如E4、A3)和时间位置(第X小节)
    """

    print(f"  发送请求到 DeepSeek API...")
    t0 = time.time()

    try:
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            timeout=120,
        )
        elapsed = time.time() - t0
        print(f"  API 响应 ({elapsed:.0f}s): HTTP {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            report = data["choices"][0]["message"]["content"]
            tokens = data.get("usage", {})
            print(f"  Tokens: prompt={tokens.get('prompt_tokens', '?')}, "
                  f"completion={tokens.get('completion_tokens', '?')}")
        else:
            print(f"  API 错误: {resp.text[:300]}")
            report = f"[API 调用失败: HTTP {resp.status_code}]\n\n{resp.text[:500]}"

    except Exception as e:
        print(f"  API 调用异常: {e}")
        report = f"[API 调用异常: {e}]"

    # 追加数据附录
    report += "\n\n---\n\n## 附录: 原始数据摘要\n\n"
    report += f"- 手型问题总数: {hand_summary['total_issues']}\n"
    report += f"- 音频分析: {_json_dumps(audio_summary, ensure_ascii=False)}\n"
    report += f"- Oemer 曲谱解析: {oemer_summary['success_pages']}/{oemer_summary['total_pages']} 页成功\n"
    report += f"- 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"- 评估设备: {DEVICE['gpu_name']}\n"

    return report


def _generate_basic_report(oemer_results, hand_issues, audio_diff):
    """无 AI 时的基础报告(纯数据汇总)。"""
    lines = [
        "# AI 琴伴 - 综合练习评估报告 (基础版)",
        "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 说明: 因 DeepSeek API 未配置,此为数据汇总报告",
        "",
        "## 一、手型分析",
        f"- 总问题数: {len(hand_issues)}",
    ]
    by_type = _group_by(hand_issues, "issue_type")
    for t, c in by_type.items():
        lines.append(f"- {t}: {c} 次")
    by_finger = _group_by(hand_issues, "finger")
    lines.append("\n### 问题分布(按手指)")
    for f, c in by_finger.items():
        lines.append(f"- {f}: {c} 次")

    lines.append("\n## 二、音频分析")
    for k, v in audio_diff.items():
        if k != "all_notes":
            lines.append(f"- {k}: {v if isinstance(v, (int, float)) else len(v)}")

    lines.append("\n## 三、曲谱解析")
    for r in oemer_results:
        lines.append(f"- 第{r['page']}页: {r['status']} ({r.get('elapsed_s', '?')}s)")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════
def main():
    start_time = datetime.now()
    print("=" * 60)
    print(" AI 琴伴 - 综合评估系统")
    print(f" 启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" 输出目录: {REPORT_DIR}")
    print(f" DeepSeek API: {'已配置' if DEEPSEEK_KEY else '未配置'}")
    print("=" * 60)

    # 1. Oemer 曲谱解析
    oemer_results, combined_midi = run_oemer_on_all()

    # 2. 手型检测 + 可视化
    hand_issues, good_frames, bad_frames = run_hand_tracking()

    # 3. 音频转录 + 比对
    audio_diff, transcribed, standard = run_audio_analysis(combined_midi)

    # 4. 生成 AI 报告
    report = generate_ai_report(oemer_results, hand_issues, audio_diff, combined_midi)

    # 5. 保存报告（命名规则：REPORT_日期_时间.md）
    report_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_filename = f"REPORT_{report_timestamp}.md"
    report_path = Path(__file__).resolve().parent / report_filename
    report_path.write_text(report, encoding="utf-8")
    print(f"\n{'=' * 60}")
    print(f" 报告已保存: {report_path}")
    print(f" 所有输出: {REPORT_DIR}")
    print(f" 总耗时: {(datetime.now() - start_time).total_seconds():.0f}s")
    print(f"{'=' * 60}")

    # 列出所有输出文件
    print("\n 输出文件清单:")
    for f in sorted(REPORT_DIR.rglob("*")):
        if f.is_file():
            size = f.stat().st_size
            size_str = f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"
            print(f"  {f.relative_to(REPORT_DIR)} ({size_str})")


if __name__ == "__main__":
    main()
