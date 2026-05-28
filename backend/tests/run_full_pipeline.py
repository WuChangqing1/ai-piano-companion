"""
Full pipeline: Oemer OMR → Hand Analysis → Audio Transcription → Comparison → HTML Report.
With pre-flight checks to validate input data before processing.

Usage:
    python tests/run_full_pipeline.py test3
    python tests/run_full_pipeline.py test2
"""
import os
import sys
import json
import glob
import math
import time
import base64
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pretty_midi
import numpy as np

# ─── Constants ─────────────────────────────────────────
TEST_DATA = Path(__file__).resolve().parent.parent / "test_data"
OEMER_EXE = "D:/App/Business/Coding/Python/Miniconda/envs/AIqinban/Scripts/oemer.exe"
PYTHON_EXE = "D:/App/Business/Coding/Python/Miniconda/envs/AIqinban/python.exe"
FRAME_INTERVAL = 0.5  # sample every 0.5s for hand analysis
TIME_TOLERANCE = 0.5   # audio comparison time window

NOTE_DURATIONS = {
    "whole": 4.0, "half": 2.0, "quarter": 1.0,
    "eighth": 0.5, "16th": 0.25, "32nd": 0.125,
}


# ═══════════════════════════════════════════════════════
# PRE-FLIGHT CHECKS
# ═══════════════════════════════════════════════════════

def run_preflight(test_dir: Path, test_name: str) -> dict:
    """Validate all input data before running the pipeline.
    Returns dict with check results and metadata.
    """
    print("\n" + "=" * 60)
    print(f" PRE-FLIGHT CHECK: {test_name}")
    print("=" * 60)

    checks = {}
    all_ok = True

    # 1. Video exists and is readable
    video_files = list(test_dir.glob("*.mp4")) + list(test_dir.glob("*.mov"))
    if not video_files:
        print("  [FAIL] No video file (.mp4/.mov) found")
        all_ok = False
    else:
        video_path = video_files[0]
        # Get video info
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-show_entries", "stream=width,height,codec_name",
             "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=30
        )
        lines = result.stdout.strip().split('\n')
        if not lines or not lines[0]:
            print(f"  [FAIL] Cannot read video metadata: {video_path.name}")
            all_ok = False
        else:
            parts = lines[0].split(',')
            width, height = int(parts[0]), int(parts[1]) if len(parts) > 1 else (0, 0)
            duration_line = lines[-1] if len(lines) > 1 else lines[0]
            duration = float(duration_line) if duration_line.replace('.','').isdigit() else 0
            checks['video'] = {
                'path': str(video_path), 'name': video_path.name,
                'width': width, 'height': height, 'duration': duration,
            }
            print(f"  [OK] Video: {video_path.name} ({width}x{height}, {duration:.1f}s)")

    # 2. Sheet music images exist
    img_files = sorted(test_dir.glob("*.jpg")) + sorted(test_dir.glob("*.png"))
    if not img_files:
        print("  [FAIL] No sheet music images (.jpg/.png) found")
        all_ok = False
    else:
        sizes = []
        for f in img_files:
            sizes.append(f.stat().st_size)
        checks['sheet_music'] = {
            'pages': len(img_files),
            'paths': [str(f) for f in img_files],
            'total_size_kb': sum(sizes) // 1024,
        }
        print(f"  [OK] Sheet music: {len(img_files)} page(s), {sum(sizes)//1024} KB total")

    # 3. Audio track in video
    if 'video' in checks:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", checks['video']['path']],
            capture_output=True, text=True, timeout=30
        )
        has_audio = 'audio' in result.stdout
        checks['has_audio'] = has_audio
        if has_audio:
            print(f"  [OK] Audio track found in video")
        else:
            print(f"  [WARN] No audio track in video - audio analysis will be skipped")

    # 4. Check Oemer CLI available
    oemer_path = Path(OEMER_EXE)
    if oemer_path.exists():
        checks['oemer_available'] = True
        print(f"  [OK] Oemer CLI found")
    else:
        checks['oemer_available'] = False
        print(f"  [WARN] Oemer CLI not found at {OEMER_EXE}")

    # 5. Check Python dependencies
    try:
        import mediapipe as mp
        checks['mediapipe'] = True
    except ImportError:
        checks['mediapipe'] = False
        print(f"  [WARN] mediapipe not installed")

    try:
        import basic_pitch
        checks['basic_pitch'] = True
    except ImportError:
        checks['basic_pitch'] = False
        print(f"  [WARN] basic-pitch not installed")

    checks['all_ok'] = all_ok
    if all_ok:
        print(f"\n  Pre-flight: ALL CHECKS PASSED")
    else:
        print(f"\n  Pre-flight: SOME CHECKS FAILED - fix before proceeding")

    return checks


# ═══════════════════════════════════════════════════════
# STAGE 1: Oemer OMR → MusicXML → MIDI
# ═══════════════════════════════════════════════════════

def _read_musicxml_tempo(mxl_path: Path) -> float:
    """Read tempo from MusicXML <sound tempo="X"/> tag. Default 120 BPM."""
    try:
        tree = ET.parse(str(mxl_path))
        root = tree.getroot()
        # Find <sound tempo="..."/> anywhere in the document
        for sound_elem in root.iter():
            if sound_elem.tag.endswith('sound'):
                tempo_str = sound_elem.get('tempo', '')
                if tempo_str:
                    tempo = float(tempo_str)
                    return tempo
        # Also check direction elements
        for direction in root.iter():
            if direction.tag.endswith('direction'):
                for sound in direction.findall('.//'):
                    if sound.tag.endswith('sound'):
                        tempo_str = sound.get('tempo', '')
                        if tempo_str:
                            return float(tempo_str)
    except Exception:
        pass
    return 120.0


def run_oemer(test_dir: Path, checks: dict) -> Path:
    """Run Oemer OMR on sheet music, convert MusicXML to MIDI with correct tempo."""
    oemer_dir = test_dir / "oemer_output"
    oemer_dir.mkdir(parents=True, exist_ok=True)
    midi_path = oemer_dir / "standard_score.mid"

    print("\n" + "=" * 60)
    print(" STAGE 1: Oemer OMR → MIDI")
    print("=" * 60)

    # Check if already done
    existing = list(oemer_dir.glob("*.musicxml"))
    if existing and midi_path.exists():
        print(f"  [SKIP] Already processed ({len(existing)} MusicXML, MIDI exists)")
        pm = pretty_midi.PrettyMIDI(str(midi_path))
        n_notes = sum(len(inst.notes) for inst in pm.instruments)
        print(f"  Standard MIDI: {n_notes} notes")
        return midi_path

    # Run Oemer per page
    results = []
    for img_path in checks['sheet_music']['paths']:
        img_file = Path(img_path)
        page_name = img_file.stem
        page_out = oemer_dir / f"page_{page_name}"
        page_out.mkdir(parents=True, exist_ok=True)

        mxl_file = page_out / f"{page_name}.musicxml"
        if mxl_file.exists():
            print(f"  Oemer {page_name}: cached → skip")
            results.append({'status': 'OK', 'output_dir': str(page_out), 'page': page_name})
            continue

        print(f"  Oemer {page_name}: running...")
        t0 = time.time()
        try:
            proc = subprocess.run(
                [OEMER_EXE, str(img_path), "-o", str(page_out), "--without-deskew"],
                capture_output=True, text=True, timeout=300,
            )
            elapsed = time.time() - t0
            if proc.returncode == 0 or mxl_file.exists():
                print(f"    OK ({elapsed:.0f}s)")
                results.append({'status': 'OK', 'output_dir': str(page_out), 'page': page_name})
            else:
                print(f"    FAILED (exit {proc.returncode})")
                results.append({'status': 'FAIL', 'output_dir': str(page_out), 'page': page_name})
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({'status': 'ERROR', 'output_dir': str(page_out), 'page': page_name})

    # Convert MusicXML → MIDI with correct tempo
    print("\n  Converting MusicXML → MIDI...")
    pm = pretty_midi.PrettyMIDI(initial_tempo=120)
    piano = pretty_midi.Instrument(program=0, name="Piano")
    all_notes = 0
    total_measures = 0
    measure_offset = 0

    for r in results:
        if r['status'] != 'OK':
            continue
        page_dir = Path(r['output_dir'])
        mxl_files = list(page_dir.glob("*.musicxml"))
        if not mxl_files:
            continue

        mxl_path = mxl_files[0]
        tempo = _read_musicxml_tempo(mxl_path)
        beat_duration = 60.0 / tempo  # seconds per beat (quarter note)
        print(f"    {r['page']}: tempo={tempo} BPM, beat={beat_duration:.3f}s")

        try:
            tree = ET.parse(str(mxl_path))
            root = tree.getroot()
        except Exception:
            continue

        page_max_measures = 0
        for part in root.findall("part"):
            measures = part.findall("measure")
            page_max_measures = max(page_max_measures, len(measures))
            tick = 0.0  # in quarter-note beats
            for measure in measures:
                for note in measure.findall("note"):
                    pitch_elem = note.find("pitch")
                    if pitch_elem is None:
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
                    start_time = beat_start * beat_duration
                    end_time = (beat_start + dur) * beat_duration

                    note_obj = pretty_midi.Note(velocity=80, pitch=midi_num, start=start_time, end=end_time)
                    piano.notes.append(note_obj)
                    all_notes += 1
                    tick += dur

        measure_offset += page_max_measures
        total_measures += page_max_measures

    pm.instruments.append(piano)
    pm.write(str(midi_path))

    duration_s = piano.notes[-1].end if piano.notes else 0
    print(f"  MIDI saved: {all_notes} notes, {total_measures} measures, {duration_s:.0f}s at {tempo} BPM")
    print(f"    → {midi_path.name}")
    return midi_path


# ═══════════════════════════════════════════════════════
# STAGE 2: Hand Analysis
# ═══════════════════════════════════════════════════════

def run_hand_analysis(test_dir: Path, checks: dict):
    """Run hand analysis via analyze_hands.py."""
    print("\n" + "=" * 60)
    print(" STAGE 2: Hand Analysis")
    print("=" * 60)

    video_path = checks['video']['path']
    report_dir = test_dir / "hand_analysis_report"

    analyze_script = Path(__file__).resolve().parent / "analyze_hands.py"
    t0 = time.time()
    result = subprocess.run(
        [PYTHON_EXE, str(analyze_script), video_path, str(report_dir)],
        capture_output=True, text=True, timeout=600, cwd=str(Path(__file__).resolve().parent.parent)
    )
    elapsed = time.time() - t0

    if result.returncode != 0:
        print(f"  [ERROR] Hand analysis failed (rc={result.returncode})")
        print(result.stderr[-500:])
        return None

    # Parse output for summary
    output = result.stdout
    for line in output.split('\n'):
        if '平均分' in line or 'Avg score' in line.lower():
            print(f"  {line.strip()}")
        if '采样帧数' in line or '问题数' in line:
            print(f"  {line.strip()}")

    json_path = report_dir / "hand_analysis_data.json"
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  Hand score: {data['avg_score']:.0f}/100 ({data['total_issues']} issues in {data['total_frames_sampled']} frames, {elapsed:.0f}s)")
        return data
    return None


# ═══════════════════════════════════════════════════════
# STAGE 3: Audio Transcription
# ═══════════════════════════════════════════════════════

def run_audio_transcription(test_dir: Path):
    """Extract audio from video and run basic-pitch transcription."""
    print("\n" + "=" * 60)
    print(" STAGE 3: Audio Transcription")
    print("=" * 60)

    audio_wav = test_dir / "test_audio.wav"
    output_dir = test_dir / "basic_pitch_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    midi_out = output_dir / "test_audio_basic_pitch.mid"

    if midi_out.exists():
        print(f"  [SKIP] Transcription already exists")
        pm = pretty_midi.PrettyMIDI(str(midi_out))
        n_notes = sum(len(inst.notes) for inst in pm.instruments)
        print(f"  Transcribed: {n_notes} notes")
        return midi_out, audio_wav

    # Check if audio was already extracted
    video_path = test_dir / "test.mp4"
    if not audio_wav.exists():
        print("  Extracting audio from video...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
             "-ar", "22050", "-ac", "1", str(audio_wav)],
            capture_output=True, timeout=60,
        )
        print(f"  Audio extracted: {audio_wav.stat().st_size // 1024} KB")

    # Run basic-pitch
    import basic_pitch
    from basic_pitch.inference import predict_and_save

    model_path = os.path.join(os.path.dirname(basic_pitch.__file__),
                              'saved_models', 'icassp_2022', 'nmp.onnx')
    print("  Running basic-pitch ONNX...")
    t0 = time.time()
    predict_and_save(
        [str(audio_wav)], str(output_dir),
        save_midi=True, sonify_midi=False,
        save_model_outputs=False, save_notes=False,
        model_or_model_path=model_path,
    )
    # The above may fail on emoji print but MIDI should be saved
    elapsed = time.time() - t0
    print(f"  Transcription done ({elapsed:.0f}s)")

    if midi_out.exists():
        pm = pretty_midi.PrettyMIDI(str(midi_out))
        n_notes = sum(len(inst.notes) for inst in pm.instruments)
        print(f"  Transcribed: {n_notes} notes")
    return midi_out, audio_wav


# ═══════════════════════════════════════════════════════
# STAGE 4: Audio Comparison
# ═══════════════════════════════════════════════════════

def run_audio_comparison(test_dir: Path, trans_midi: Path, std_midi: Path):
    """Compare transcribed MIDI with standard score MIDI."""
    print("\n" + "=" * 60)
    print(" STAGE 4: Audio Comparison")
    print("=" * 60)

    def extract(midi_path, label):
        pm = pretty_midi.PrettyMIDI(str(midi_path))
        notes = []
        for inst in pm.instruments:
            for n in inst.notes:
                notes.append({
                    'pitch': n.pitch, 'start': n.start, 'end': n.end,
                    'duration': n.end - n.start, 'velocity': n.velocity,
                    'note_name': pretty_midi.note_number_to_name(n.pitch),
                })
        notes.sort(key=lambda n: n['start'])
        end_t = notes[-1]['end'] if notes else 0
        print(f"  [{label}] {len(notes)} notes, {end_t:.1f}s")
        return notes, pm

    trans_notes, trans_pm = extract(trans_midi, "Transcribed")
    std_notes, std_pm = extract(std_midi, "Standard")

    # Find best time offset
    best_offset = 0.0
    best_count = 0
    max_offset = min(5.0, std_notes[-1]['start'] * 0.2) if std_notes else 5.0
    for off in np.arange(0, max_offset + 0.05, 0.05):
        count = 0
        si = 0
        for tn in trans_notes:
            tn_t = tn['start'] - off
            if tn_t < 0:
                continue
            while si < len(std_notes) and std_notes[si]['start'] < tn_t - TIME_TOLERANCE:
                si += 1
            for sj in range(si, len(std_notes)):
                if std_notes[sj]['start'] > tn_t + TIME_TOLERANCE:
                    break
                if abs(tn['pitch'] - std_notes[sj]['pitch']) % 12 == 0:
                    count += 1
                    break
        if count > best_count:
            best_count, best_offset = count, off

    print(f"  Best offset: {best_offset:.2f}s ({best_count} octave matches)")

    # Detailed comparison
    matched_std, matched_trans = set(), set()
    correct, pitch_errors = [], []

    for ti, tn in enumerate(trans_notes):
        tn_t = tn['start'] - best_offset
        if tn_t < 0:
            continue
        best_dist = float('inf')
        best_si = -1
        for si, sn in enumerate(std_notes):
            if si in matched_std:
                continue
            td = abs(tn_t - sn['start'])
            if td > TIME_TOLERANCE:
                continue
            dist = td / TIME_TOLERANCE + abs(tn['pitch'] - sn['pitch']) / 12.0
            if dist < best_dist:
                best_dist, best_si = dist, si
        if best_si >= 0:
            matched_trans.add(ti)
            matched_std.add(best_si)
            sn = std_notes[best_si]
            if abs(tn['pitch'] - sn['pitch']) == 0:
                correct.append({
                    'pitch': tn['pitch'], 'note_name': tn['note_name'],
                    'std_start': sn['start'],
                    'time_diff': round(abs(tn_t - sn['start']), 3),
                })
            else:
                pitch_errors.append({
                    'expected_pitch': sn['pitch'], 'expected_name': sn['note_name'],
                    'played_pitch': tn['pitch'], 'played_name': tn['note_name'],
                    'pitch_diff': abs(tn['pitch'] - sn['pitch']),
                    'std_start': sn['start'],
                    'time_diff': round(abs(tn_t - sn['start']), 3),
                })

    missing = [std_notes[si] for si in range(len(std_notes)) if si not in matched_std]
    extra = [trans_notes[ti] for ti in range(len(trans_notes)) if ti not in matched_trans]

    nc, npe = len(correct), len(pitch_errors)
    nm, ne = len(missing), len(extra)
    n_trans, n_std = len(trans_notes), len(std_notes)
    n_matched = nc + npe

    precision = nc / n_trans * 100 if n_trans else 0
    recall = nc / n_std * 100 if n_std else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    std_tempo = std_pm.estimate_tempo()
    trans_tempo = trans_pm.estimate_tempo()
    tempo_diff = abs(std_tempo - trans_tempo)
    tempo_score = max(0, 100 - tempo_diff * 2)
    pitch_score = round(recall * 0.7 + precision * 0.3)
    overall = round(pitch_score * 0.5 + tempo_score * 0.5)

    print(f"  Time-matched: {n_matched} | Correct: {nc} | Wrong pitch: {npe}")
    print(f"  Missing: {nm} | Extra: {ne}")
    print(f"  Precision: {precision:.1f}% | Recall: {recall:.1f}% | F1: {f1:.1f}%")
    print(f"  Tempo: std={std_tempo:.1f} trans={trans_tempo:.1f} (diff={tempo_diff:.1f} BPM)")
    print(f"  Scores: pitch={pitch_score} tempo={tempo_score:.0f} overall={overall}")

    output = {
        'start_offset': best_offset,
        'standard_note_count': n_std, 'transcribed_note_count': n_trans,
        'time_matched_count': n_matched,
        'correct_count': nc, 'pitch_error_count': npe,
        'missing_count': nm, 'extra_count': ne,
        'time_match_rate': round(n_matched / max(n_std, n_trans) * 100, 1) if max(n_std, n_trans) else 0,
        'precision': round(precision, 1), 'recall': round(recall, 1),
        'f1_score': round(f1, 1),
        'pitch_score': pitch_score, 'tempo_score': round(tempo_score),
        'overall_audio_score': overall,
        'tempo': {
            'standard_tempo_bpm': round(std_tempo, 1),
            'transcribed_tempo_bpm': round(trans_tempo, 1),
            'tempo_ratio': round(trans_tempo / std_tempo, 3) if std_tempo else 1.0,
        },
        'pitch_errors_detail': pitch_errors[:30],
        'missing_notes_detail': [{'pitch': n['pitch'], 'note_name': n['note_name'], 'start': round(n['start'], 2)} for n in missing[:30]],
        'extra_notes_detail': [{'pitch': n['pitch'], 'note_name': n['note_name'], 'start': round(n['start'], 2)} for n in extra[:30]],
    }

    json_path = test_dir / "audio_comparison.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {json_path.name}")
    return output


# ═══════════════════════════════════════════════════════
# STAGE 5: HTML Report
# ═══════════════════════════════════════════════════════

def generate_html_report(test_dir: Path, hand_data: dict, audio_data: dict, test_name: str):
    """Generate final HTML report with embedded hand images."""
    print("\n" + "=" * 60)
    print(" STAGE 5: HTML Report")
    print("=" * 60)

    hand_score = round(hand_data['avg_score'])
    audio_score = audio_data['overall_audio_score']
    overall = round(hand_score * 0.5 + audio_score * 0.5)

    report_dir = test_dir / "hand_analysis_report"

    # Encode worst 5 images
    worst5_b64 = []
    worst5_data = hand_data.get('worst_5', [])
    for wf in worst5_data:
        img_rel = wf.get('worst_image_path', '')
        if img_rel:
            img_path = report_dir / img_rel
            if img_path.exists():
                with open(img_path, 'rb') as f:
                    worst5_b64.append(base64.b64encode(f.read()).decode('ascii'))

    # Helpers
    def sc(s):
        if s >= 90: return '#22c55e'
        if s >= 75: return '#3b82f6'
        if s >= 60: return '#f59e0b'
        return '#ef4444'

    def sl(s):
        if s >= 90: return '优秀'
        if s >= 75: return '良好'
        if s >= 60: return '及格'
        return '需要加强'

    def itn(t):
        return {
            'folded_finger': '折指（PIP关节过度弯曲）',
            'collapsed_knuckle': '掌关节塌陷',
            'over_extended': '手指过度伸直',
            'thumb_tucked': '拇指内扣',
        }.get(t, t)

    def badge(t):
        return '<span class="badge badge-danger">严重</span>' if t in ('folded_finger', 'collapsed_knuckle') else '<span class="badge badge-warning">轻度</span>'

    tempo = audio_data['tempo']
    tm = audio_data.get('time_matched_count', audio_data['correct_count'] + audio_data['pitch_error_count'])
    tdiff = abs(tempo['standard_tempo_bpm'] - tempo['transcribed_tempo_bpm'])
    page_count = len(glob.glob(os.path.join(str(test_dir), '*.jpg'))) + len(glob.glob(os.path.join(str(test_dir), '*.png')))

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 琴伴 - 综合评估报告</title>
<style>
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; background:#f0f2f5;color:#1a1a2e;line-height:1.6; }}
.container {{ max-width:800px;margin:0 auto;padding:20px; }}
.header {{ background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border-radius:16px;padding:32px 28px;margin-bottom:20px;text-align:center; }}
.header h1 {{ font-size:26px;font-weight:700;margin-bottom:8px; }}
.header .subtitle {{ font-size:13px;opacity:.85; }}
.score-row {{ display:flex;gap:12px;margin-bottom:20px; }}
.score-card {{ flex:1;background:white;border-radius:14px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.score-card .label {{ font-size:13px;color:#6b7280;margin-bottom:8px; }}
.score-card .value {{ font-size:36px;font-weight:800; }}
.score-card .grade {{ font-size:12px;margin-top:4px; }}
.score-card .bar {{ height:6px;border-radius:3px;margin-top:10px;overflow:hidden;background:#e5e7eb; }}
.score-card .bar-fill {{ height:100%;border-radius:3px; }}
.section {{ background:white;border-radius:14px;padding:28px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06); }}
.section h2 {{ font-size:20px;font-weight:700;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid #f0f0f5; }}
.section h3 {{ font-size:16px;font-weight:600;margin:24px 0 12px;color:#374151; }}
.section h4 {{ font-size:15px;font-weight:600;margin:20px 0 10px;color:#4b5563; }}
table {{ width:100%;border-collapse:collapse;margin:12px 0;font-size:14px; }}
th,td {{ padding:10px 14px;text-align:left;border-bottom:1px solid #f3f4f6; }}
th {{ background:#f9fafb;font-weight:600;color:#6b7280;font-size:13px; }}
tr:hover td {{ background:#fafbff; }}
.badge {{ display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600; }}
.badge-danger {{ background:#fee2e2;color:#dc2626; }}
.badge-warning {{ background:#fef3c7;color:#d97706; }}
.badge-success {{ background:#d1fae5;color:#059669; }}
.frame-card {{ border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:16px 0;background:#fafbfc; }}
.frame-card img {{ width:100%;border-radius:8px;margin-top:12px;border:1px solid #e5e7eb; }}
.frame-meta {{ display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:#6b7280;margin:8px 0; }}
.advice-list {{ list-style:none;padding:0; }}
.advice-list li {{ padding:10px 14px;margin:6px 0;background:#f9fafb;border-left:3px solid #667eea;border-radius:0 8px 8px 0;font-size:14px; }}
.footer {{ text-align:center;padding:20px;color:#9ca3af;font-size:12px; }}
.issue-grid {{ display:grid;grid-template-columns:1fr 1fr;gap:10px; }}
.issue-item {{ padding:10px 14px;background:#f9fafb;border-radius:8px;font-size:13px;display:flex;justify-content:space-between;align-items:center; }}
.issue-item .count {{ font-weight:700;font-size:16px; }}
@media(max-width:600px){{ .score-row{{flex-direction:column;}} .issue-grid{{grid-template-columns:1fr;}} }}
</style>
</head>
<body><div class="container">

<div class="header">
<h1>AI 琴伴 · 综合评估报告</h1>
<div class="subtitle">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp;|&nbsp; {test_name} ({hand_data['duration_s']:.0f}s · {hand_data['resolution']} · {page_count}页曲谱)</div>
</div>

<div class="score-row">
<div class="score-card"><div class="label">手型</div><div class="value" style="color:{sc(hand_score)}">{hand_score}</div><div class="grade" style="color:{sc(hand_score)}">{sl(hand_score)}</div><div class="bar"><div class="bar-fill" style="width:{hand_score}%;background:{sc(hand_score)}"></div></div></div>
<div class="score-card"><div class="label">音频</div><div class="value" style="color:{sc(audio_score)}">{audio_score}</div><div class="grade" style="color:{sc(audio_score)}">{sl(audio_score)}</div><div class="bar"><div class="bar-fill" style="width:{audio_score}%;background:{sc(audio_score)}"></div></div></div>
<div class="score-card"><div class="label">综合</div><div class="value" style="color:{sc(overall)}">{overall}</div><div class="grade" style="color:{sc(overall)}">{sl(overall)}</div><div class="bar"><div class="bar-fill" style="width:{overall}%;background:{sc(overall)}"></div></div></div>
</div>

<div class="section"><h2>一、手型分析</h2>
<h3>1.1 视频概览</h3>
<table>
<tr><th style="width:40%">指标</th><th>数值</th></tr>
<tr><td>视频</td><td>{hand_data['video']}</td></tr>
<tr><td>视频时长</td><td>{hand_data['duration_s']}s</td></tr>
<tr><td>帧率</td><td>{hand_data['fps']} FPS</td></tr>
<tr><td>分辨率</td><td>{hand_data['resolution']}</td></tr>
<tr><td>采样帧数</td><td>{hand_data['total_frames_sampled']}</td></tr>
<tr><td>检测到手的帧数</td><td>{hand_data['frames_with_hands']}</td></tr>
<tr><td>检测到手的总次数</td><td>{hand_data['total_hands_detected']}</td></tr>
<tr><td>过滤非弹奏帧</td><td>{hand_data.get('skipped_by_filter', 0)}</td></tr>
<tr style="font-weight:700"><td>平均手型分</td><td style="color:{sc(hand_score)};font-size:18px">{hand_score} / 100</td></tr>
<tr><td>最佳 / 最差帧</td><td>{hand_data['best_score']:.0f} / {hand_data['worst_score']:.0f}</td></tr>
</table>

<h3>1.2 问题类型分布</h3>
<div class="issue-grid">'''

    for t, c in sorted(hand_data.get('issues_by_type', {}).items(), key=lambda x: -x[1]):
        html += f'<div class="issue-item"><span>{itn(t)}</span><span class="count" style="color:{sc(100 - c * 3)}">{c}</span></div>'

    html += '</div><h3>1.3 问题手指分布</h3><table><tr><th>手指</th><th>问题次数</th></tr>'
    for f, c in sorted(hand_data.get('issues_by_finger', {}).items(), key=lambda x: -x[1]):
        html += f'<tr><td>{f}</td><td>{c}</td></tr>'
    html += '</table><h3>1.4 手型最差 5 帧（骨架标注）</h3>'

    for i, wf in enumerate(worst5_data):
        s = wf['score']; issues = wf.get('issues', [])
        img_src = f'data:image/jpeg;base64,{worst5_b64[i]}' if i < len(worst5_b64) else ''
        html += f'''<div class="frame-card"><h4>第 {i+1} 名 — 得分: <span style="color:{sc(s)}">{s:.0f} / 100</span></h4>
<div class="frame-meta"><span>时间: {wf["timestamp"]}s</span><span>小节: {wf.get("measure","?")}</span><span>检测到手: {wf.get("hands_detected",0)}</span><span>问题数: {len(issues)}</span></div>'''
        if issues:
            html += '<table><tr><th>手</th><th>手指</th><th>问题类型</th><th>严重度</th></tr>'
            for iss in issues:
                html += f'<tr><td>{iss.get("hand","")}</td><td>{iss.get("finger","")}</td><td>{itn(iss.get("type",""))}</td><td>{badge(iss.get("type",""))}</td></tr>'
            html += '</table>'
        if img_src:
            html += f'<img src="{img_src}" loading="lazy">'
        html += '</div>'

    html += f'''</div>

<div class="section"><h2>二、音频分析</h2>
<h3>2.1 数据概览</h3>
<table>
<tr><th style="width:40%">指标</th><th>数值</th></tr>
<tr><td>曲谱解析方式</td><td>Oemer ONNX (OMR)</td></tr>
<tr><td>标准曲谱音符数</td><td>{audio_data["standard_note_count"]}</td></tr>
<tr><td>音频转录方式</td><td>basic-pitch ONNX</td></tr>
<tr><td>转录音符数</td><td>{audio_data["transcribed_note_count"]}</td></tr>
<tr><td>起始偏移（自动对齐）</td><td>{audio_data.get("start_offset",0)}s</td></tr>
<tr><td>时间匹配容差</td><td>{TIME_TOLERANCE}s</td></tr>
</table>

<h3>2.2 比对结果</h3>
<table>
<tr><th>类别</th><th>数量</th><th>说明</th></tr>
<tr><td>时间匹配</td><td>{tm}</td><td>音频与曲谱在时间上对齐</td></tr>
<tr><td><span class="badge badge-success">正确</span></td><td><b>{audio_data["correct_count"]}</b></td><td>时间和音高完全匹配</td></tr>
<tr><td><span class="badge badge-warning">错音</span></td><td><b>{audio_data["pitch_error_count"]}</b></td><td>时间对上但弹了不同的音</td></tr>
<tr><td><span class="badge badge-danger">漏音</span></td><td><b>{audio_data["missing_count"]}</b></td><td>标准曲谱有但未弹奏</td></tr>
<tr><td>多余音</td><td><b>{audio_data["extra_count"]}</b></td><td>弹了但曲谱上不存在的音</td></tr>
</table>

<h3>2.3 音频评分</h3>
<table>
<tr><th>指标</th><th>分数</th><th>等级</th></tr>
<tr><td>音高准确率</td><td style="color:{sc(audio_data['pitch_score'])};font-weight:700">{audio_data["pitch_score"]} / 100</td><td><span class="badge badge-{"success" if audio_data["pitch_score"]>=90 else "warning" if audio_data["pitch_score"]>=60 else "danger"}">{sl(audio_data["pitch_score"])}</span></td></tr>
<tr><td>节奏准确率</td><td style="color:{sc(audio_data['tempo_score'])};font-weight:700">{audio_data["tempo_score"]} / 100</td><td><span class="badge badge-{"success" if audio_data["tempo_score"]>=90 else "warning"}">{sl(audio_data["tempo_score"])}</span></td></tr>
<tr style="font-weight:700"><td>综合音频分</td><td style="color:{sc(audio_score)};font-size:18px">{audio_score} / 100</td><td><span class="badge badge-{"success" if audio_score>=90 else "warning" if audio_score>=60 else "danger"}">{sl(audio_score)}</span></td></tr>
</table>

<h3>2.4 节奏分析</h3>
<table>
<tr><th style="width:40%">指标</th><th>数值</th></tr>
<tr><td>标准曲速</td><td>{tempo["standard_tempo_bpm"]} BPM</td></tr>
<tr><td>实际弹奏速度</td><td>{tempo["transcribed_tempo_bpm"]} BPM</td></tr>
<tr><td>速度比</td><td>{tempo["tempo_ratio"]}</td></tr>
<tr><td>速度偏差</td><td>{tdiff:.1f} BPM</td></tr>
</table>'''

    pe = audio_data.get('pitch_errors_detail', [])
    if pe:
        html += '<h3>2.5 错音示例</h3><table><tr><th>时间</th><th>标准音</th><th>实际弹奏</th><th>偏差</th></tr>'
        for p in pe[:15]:
            html += f'<tr><td>{p["std_start"]:.2f}s</td><td><b>{p["expected_name"]}</b> ({p["expected_pitch"]})</td><td><b>{p["played_name"]}</b> ({p["played_pitch"]})</td><td>{p["pitch_diff"]}半音</td></tr>'
        html += '</table>'

    mn = audio_data.get('missing_notes_detail', [])
    en = audio_data.get('extra_notes_detail', [])
    if mn and en:
        html += '<div style="display:flex;gap:16px;flex-wrap:wrap"><div style="flex:1;min-width:280px"><h3>2.6 漏音</h3><table><tr><th>时间</th><th>音名</th><th>音高</th></tr>'
        for m in mn[:15]:
            html += f'<tr><td>{m["start"]:.2f}s</td><td>{m["note_name"]}</td><td>{m["pitch"]}</td></tr>'
        html += '</table></div><div style="flex:1;min-width:280px"><h3>2.7 多余音</h3><table><tr><th>时间</th><th>音名</th><th>音高</th></tr>'
        for e in en[:15]:
            html += f'<tr><td>{e["start"]:.2f}s</td><td>{e["note_name"]}</td><td>{e["pitch"]}</td></tr>'
        html += '</table></div></div>'

    ibt = hand_data.get('issues_by_type', {})
    html += '</div><div class="section"><h2>三、练习建议</h2><ul class="advice-list">'
    if ibt.get('folded_finger', 0): html += f'<li><b>折指（{ibt["folded_finger"]}次）</b>：手指第一关节（PIP）过度弯曲。建议「高抬指」练习，保持掌关节支撑。</li>'
    if ibt.get('collapsed_knuckle', 0): html += f'<li><b>掌关节塌陷（{ibt["collapsed_knuckle"]}次）</b>：手掌支撑不足。练习「握球手型」。</li>'
    if ibt.get('over_extended', 0): html += f'<li><b>手指过度伸直（{ibt["over_extended"]}次）</b>：缺乏自然弯曲弧度，可对着镜子慢练。</li>'
    if ibt.get('thumb_tucked', 0): html += f'<li><b>拇指内扣（{ibt["thumb_tucked"]}次）</b>：拇指应自然外展，与食指形成C形。</li>'
    if audio_data['tempo_score'] >= 90: html += f'<li><b>节奏（{audio_data["tempo_score"]}/100）</b>：优秀！与标准曲速偏差仅 {tdiff:.1f} BPM。</li>'
    else: html += f'<li><b>节奏（{audio_data["tempo_score"]}/100）</b>：与标准曲速偏差 {tdiff:.1f} BPM，建议节拍器慢练。</li>'
    if audio_data['pitch_score'] < 50: html += f'<li><b>音准（{audio_data["pitch_score"]}/100）</b>：匹配度较低，建议分手慢练，对照曲谱逐小节检查。</li>'
    html += f'''</ul></div>
<div class="section" style="text-align:center"><h2 style="border:none;justify-content:center">评分汇总</h2>
<table><tr><th>维度</th><th>手型</th><th>音准</th><th>节奏</th><th>综合</th></tr>
<tr><td><b>分数</b></td><td style="color:{sc(hand_score)};font-weight:700;font-size:16px">{hand_score}</td><td style="color:{sc(audio_data["pitch_score"])};font-weight:700;font-size:16px">{audio_data["pitch_score"]}</td><td style="color:{sc(audio_data["tempo_score"])};font-weight:700;font-size:16px">{audio_data["tempo_score"]}</td><td style="color:{sc(overall)};font-weight:700;font-size:18px">{overall}</td></tr>
<tr><td><b>等级</b></td><td><span class="badge badge-success">{sl(hand_score)}</span></td><td><span class="badge badge-{"success" if audio_data["pitch_score"]>=90 else "warning" if audio_data["pitch_score"]>=60 else "danger"}">{sl(audio_data["pitch_score"])}</span></td><td><span class="badge badge-{"success" if audio_data["tempo_score"]>=90 else "warning"}">{sl(audio_data["tempo_score"])}</span></td><td><span class="badge badge-{"success" if overall>=90 else "warning" if overall>=60 else "danger"}" style="font-size:14px;padding:4px 14px">{sl(overall)}</span></td></tr>
</table></div><div class="footer">AI 琴伴综合评估系统 · 自动生成</div></div></body></html>'''

    html_path = test_dir / "COMPREHENSIVE_REPORT.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size = os.path.getsize(html_path)
    print(f"  Report: {html_path.name} ({file_size/1024:.0f} KB)")
    print(f"  Hand: {hand_score} | Audio: {audio_score} | Overall: {overall}")
    return str(html_path)


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

def main():
    test_name = sys.argv[1] if len(sys.argv) > 1 else "test2"
    test_dir = TEST_DATA / test_name

    if not test_dir.exists():
        print(f"ERROR: Test directory not found: {test_dir}")
        sys.exit(1)

    print("=" * 60)
    print(f" AI 琴伴 - 全流程测试管线")
    print(f" 目标: {test_name}")
    print(f" 路径: {test_dir}")
    print("=" * 60)

    t_total = time.time()

    # --- Pre-flight ---
    checks = run_preflight(test_dir, test_name)
    if not checks['all_ok']:
        print("\n[ABORT] Pre-flight checks failed. Fix issues and retry.")
        sys.exit(1)

    # --- Stage 1: Oemer ---
    std_midi = run_oemer(test_dir, checks)

    # --- Stage 2: Hand Analysis ---
    hand_data = run_hand_analysis(test_dir, checks)
    if hand_data is None:
        print("\n[ERROR] Hand analysis failed.")
        sys.exit(1)

    # --- Stage 3: Audio Transcription ---
    if checks.get('has_audio', False):
        trans_midi, audio_wav = run_audio_transcription(test_dir)
    else:
        print("\n[SKIP] Stage 3: No audio track in video")
        trans_midi = None

    # --- Stage 4: Audio Comparison ---
    if trans_midi and trans_midi.exists():
        audio_data = run_audio_comparison(test_dir, trans_midi, std_midi)
    else:
        print("\n[SKIP] Stage 4: No transcription to compare")
        audio_data = {
            'overall_audio_score': 0, 'standard_note_count': 0, 'transcribed_note_count': 0,
            'correct_count': 0, 'pitch_error_count': 0, 'missing_count': 0, 'extra_count': 0,
            'time_matched_count': 0, 'precision': 0, 'recall': 0, 'f1_score': 0,
            'pitch_score': 0, 'tempo_score': 0, 'start_offset': 0,
            'tempo': {'standard_tempo_bpm': 0, 'transcribed_tempo_bpm': 0, 'tempo_ratio': 0},
            'pitch_errors_detail': [], 'missing_notes_detail': [], 'extra_notes_detail': [],
        }

    # --- Stage 5: HTML Report ---
    html_path = generate_html_report(test_dir, hand_data, audio_data, test_name)

    total_elapsed = time.time() - t_total
    print(f"\n{'=' * 60}")
    print(f" PIPELINE COMPLETE ({total_elapsed:.0f}s)")
    print(f" Report: {html_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
