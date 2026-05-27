"""AI 模型逐模块测试脚本。
用法: conda run -n AIqinban --cwd backend python tests/test_models.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TEST_DATA = Path(__file__).resolve().parent.parent / "test_data"
VIDEO = TEST_DATA / "test.mp4"
SCORES = [TEST_DATA / f"{i}.jpg" for i in (1, 2, 3)]

OK = "[OK]"
FAIL = "[FAIL]"
MOCK = "[MOCK]"


def test_hand_tracker():
    print("\n" + "=" * 55)
    print(" 1/3  Hand Tracking (MediaPipe Hands)")
    print("=" * 55)
    from ai_models.hand_tracker import detect_hand_issues

    if not VIDEO.exists():
        print(f"  SKIP: video not found ({VIDEO})")
        return False

    # 先检测真实模型是否可用
    try:
        import mediapipe as mp
        _ = mp.solutions.hands
        real_available = True
    except Exception:
        real_available = False

    issues = detect_hand_issues(VIDEO)
    tag = OK if real_available else MOCK
    print(f"  Model: {'MediaPipe (real)' if real_available else 'Mock fallback'} {tag}")
    print(f"  Issues found: {len(issues)}")
    if not issues:
        print("  Result: Clean hands, no issues detected!")
    for i in issues:
        print(f"    - m.{i['measure']} [{i['issue_type']}] {i['description']}")
    return real_available


def test_audio_amt():
    print("\n" + "=" * 55)
    print(" 2/3  Audio Transcription (basic-pitch)")
    print("=" * 55)
    from ai_models.audio_amt import transcribe_and_diff

    if not VIDEO.exists():
        print(f"  SKIP: video not found ({VIDEO})")
        return False

    try:
        from basic_pitch.inference import predict
        real_available = True
    except Exception:
        real_available = False

    result = transcribe_and_diff(VIDEO)
    tag = OK if real_available else MOCK
    print(f"  Model: {'basic-pitch ONNX (real)' if real_available else 'Mock fallback'} {tag}")
    print(f"  Duration: {result['duration']}s")
    print(f"  Wrong notes: {len(result['wrong'])}")
    print(f"  Missing notes: {len(result['missing'])}")
    print(f"  Extra notes: {len(result['extra'])}")
    print(f"  Rhythm score: {result['rhythm_score']}/100")
    return real_available


def test_omr():
    print("\n" + "=" * 55)
    print(" 3/3  Score Parsing (Oemer)")
    print("=" * 55)
    from ai_models.omr_parser import parse_score, _MOCK_FALLBACK

    # 先把 mock 标记重置，确保每次测试都尝试真实模型
    import ai_models.omr_parser as omr_mod
    omr_mod._MOCK_FALLBACK = False

    for score_file in SCORES:
        if not score_file.exists():
            print(f"  SKIP: file not found ({score_file})")
            continue
        print(f"  Input: {score_file.name}")
        result = parse_score(score_file)
        is_mock = result.get("measure_count") == 24 and omr_mod._MOCK_FALLBACK
        tag = MOCK if is_mock else OK
        print(f"    score_uid: {result['score_uid']}")
        print(f"    measures:  {result['measure_count']} {tag}")
        if not is_mock:
            print(f"    midi:      {result['midi_path']}")

    return not omr_mod._MOCK_FALLBACK


if __name__ == "__main__":
    print("=" * 55)
    print(" AI Model Test Suite")
    print(f" Video: {VIDEO.name}")
    print(f" Scores: {', '.join(s.name for s in SCORES)}")
    print("=" * 55)

    hand_ok = test_hand_tracker()
    audio_ok = test_audio_amt()
    omr_ok = test_omr()

    print("\n" + "=" * 55)
    print(" SUMMARY")
    print("=" * 55)
    print(f"  Hand Tracking:  {'REAL' if hand_ok else 'MOCK (real model failed)'}")
    print(f"  Audio Transc.:  {'REAL' if audio_ok else 'MOCK (real model failed)'}")
    print(f"  Score Parsing:  {'REAL' if omr_ok else 'MOCK (real model failed)'}")
    print("=" * 55)
