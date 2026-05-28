"""Generate comprehensive combined report: hand analysis + audio comparison + embedded images."""
import os
import sys
import json
import base64
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

TEST2_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'test2')
HAND_JSON = os.path.join(TEST2_DIR, 'hand_analysis_report', 'hand_analysis_data.json')
AUDIO_JSON = os.path.join(TEST2_DIR, 'audio_comparison.json')
REPORT_DIR = os.path.join(TEST2_DIR, 'hand_analysis_report')
OUTPUT_REPORT = os.path.join(TEST2_DIR, 'COMPREHENSIVE_REPORT.md')


def img_to_base64(path):
    """Convert image to base64 data URI."""
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def score_bar(score, width=20):
    filled = int(score / 100 * width)
    return '█' * filled + '░' * (width - filled)


def score_label(score):
    if score >= 90: return '优秀'
    if score >= 75: return '良好'
    if score >= 60: return '及格'
    return '需要加强'


def severity_label(issue_type):
    if issue_type in ('folded_finger', 'collapsed_knuckle'):
        return '🔴 严重'
    return '🟡 轻度'


def main():
    print("Loading data...")
    hand = load_json(HAND_JSON)
    audio = load_json(AUDIO_JSON)

    hand_score = round(hand['avg_score'])
    audio_score = audio['overall_audio_score']
    overall = round(hand_score * 0.5 + audio_score * 0.5)

    # Encode worst_5 images
    print("Encoding worst_5 images to base64...")
    worst5_images_b64 = {}
    worst5_data = hand.get('worst_5', [])
    for i, wf in enumerate(worst5_data):
        img_rel = wf.get('worst_image_path', '')
        if img_rel:
            img_path = os.path.join(REPORT_DIR, img_rel)
            if os.path.exists(img_path):
                b64 = img_to_base64(img_path)
                worst5_images_b64[i] = b64
                print(f"  worst_{i+1}: {len(b64)} chars")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ========== Build Report ==========
    lines = []
    def w(s=""):
        lines.append(s)

    w("# AI 琴伴 - 综合评估报告")
    w()
    w(f"> 生成时间: {now}")
    w(f"> 测试数据: `test2/` ({hand['duration_s']:.0f}s {hand['resolution']}视频 + 2页曲谱)")
    w()
    w("---")
    w()

    # ===== Executive Summary =====
    w("## 总览")
    w()
    w(f"| 维度 | 分数 | 等级 | 进度条 |")
    w(f"|------|------|------|--------|")
    w(f"| **手型** | **{hand_score} / 100** | {score_label(hand_score)} | {score_bar(hand_score)} |")
    w(f"| **音频** | **{audio_score} / 100** | {score_label(audio_score)} | {score_bar(audio_score)} |")
    w(f"| **综合** | **{overall} / 100** | {score_label(overall)} | {score_bar(overall)} |")
    w()

    # ===== Section 1: Hand Analysis =====
    w("---")
    w()
    w("## 一、手型分析")
    w()
    w("### 1.1 视频概览")
    w()
    w(f"| 指标 | 数值 |")
    w(f"|------|------|")
    w(f"| 视频 | {hand['video']} |")
    w(f"| 视频时长 | {hand['duration_s']}s |")
    w(f"| 帧率 | {hand['fps']} FPS |")
    w(f"| 分辨率 | {hand['resolution']} |")
    w(f"| 采样帧数 | {hand['total_frames_sampled']} |")
    w(f"| 检测到手的帧数 | {hand['frames_with_hands']} |")
    w(f"| 检测到手的总次数 | {hand['total_hands_detected']} |")
    w(f"| 过滤掉的非弹奏帧 | {hand.get('skipped_by_filter', 0)} |")
    w(f"| **平均手型分** | **{hand_score} / 100** |")
    w(f"| 最佳帧得分 | {hand['best_score']:.0f} / 100 |")
    w(f"| 最差帧得分 | {hand['worst_score']:.0f} / 100 |")
    w(f"| 检测到的问题总数 | {hand['total_issues']} |")
    w()

    # Issue type distribution
    w("### 1.2 问题类型分布")
    w()
    issues_by_type = hand.get('issues_by_type', {})
    if issues_by_type:
        type_desc = {
            'folded_finger': '手指折指（PIP关节过度弯曲）',
            'collapsed_knuckle': '掌关节塌陷（MCP低于PIP）',
            'over_extended': '手指过度伸直（缺乏自然弧度）',
            'thumb_tucked': '拇指内扣',
        }
        w(f"| 问题类型 | 次数 | 说明 |")
        w(f"|----------|------|------|")
        for t, c in sorted(issues_by_type.items(), key=lambda x: -x[1]):
            w(f"| {t} | {c} | {type_desc.get(t, t)} |")
    w()

    # Issue finger distribution
    issues_by_finger = hand.get('issues_by_finger', {})
    if issues_by_finger:
        w("### 1.3 问题手指分布")
        w()
        w(f"| 手指 | 问题次数 |")
        w(f"|------|----------|")
        for finger, c in sorted(issues_by_finger.items(), key=lambda x: -x[1]):
            w(f"| {finger} | {c} |")
        w()

    # Worst 5 frames
    w("### 1.4 手型最差 5 帧（含骨架标注图）")
    w()
    w("> 以下为本次分析中手型问题最严重的 5 个时刻，均带有 MediaPipe 21点红色骨架标注。")
    w()

    for i, wf in enumerate(worst5_data):
        rank = i + 1
        score = wf['score']
        timestamp = wf['timestamp']
        measure = wf.get('measure', '?')
        hands = wf.get('hands_detected', 0)
        issues = wf.get('issues', [])

        w(f"#### 第 {rank} 名 — 得分: {score:.0f} / 100")
        w()
        w(f"- **时间戳**: {timestamp}s（第 {measure} 小节）")
        w(f"- **检测到手数**: {hands}")
        w(f"- **问题数**: {len(issues)}")
        w()

        if issues:
            w(f"| # | 手 | 手指 | 问题类型 | 严重度 |")
            w(f"|---|-----|------|----------|--------|")
            for j, iss in enumerate(issues):
                t = iss.get('type', '')
                w(f"| {j+1} | {iss.get('hand', '')} | {iss.get('finger', '')} | {t} | {severity_label(t)} |")

        w()
        # Embed image
        if i in worst5_images_b64:
            w(f"![手型最差帧 {rank}](data:image/jpeg;base64,{worst5_images_b64[i]})")
            w()

    # ===== Section 2: Audio Analysis =====
    w("---")
    w()
    w("## 二、音频分析")
    w()

    w("### 2.1 数据概览")
    w()
    w(f"| 指标 | 数值 |")
    w(f"|------|------|")
    w(f"| 曲谱解析方式 | Oemer ONNX (OMR) |")
    w(f"| 标准曲谱音符数 | {audio['standard_note_count']} |")
    w(f"| 音频转录方式 | basic-pitch ONNX |")
    w(f"| 转录音符数 | {audio['transcribed_note_count']} |")
    w(f"| 起始偏移（自动对齐） | {audio.get('start_offset', 0)}s |")
    w(f"| 时间匹配容差 | 0.5s |")
    w()

    w("### 2.2 比对结果")
    w()
    n_total = max(audio['standard_note_count'], audio['transcribed_note_count'])
    tm = audio.get('time_matched_count', audio['correct_count'] + audio['pitch_error_count'])
    w(f"| 类别 | 数量 | 说明 |")
    w(f"|------|------|------|")
    w(f"| 时间匹配 | {tm} | 音频与曲谱在时间上对齐的音符数 |")
    w(f"| **正确（音高一致）** | **{audio['correct_count']}** | 时间和音高都匹配 |")
    w(f"| 错音（音高不对） | {audio['pitch_error_count']} | 时间对上但弹了不同的音 |")
    w(f"| 漏音（标准有但未弹） | {audio['missing_count']} | 标准曲谱有但实际演奏缺失 |")
    w(f"| 多余音（弹了但标准无） | {audio['extra_count']} | 实际弹了但曲谱上没有 |")
    w()

    w("### 2.3 音频评分")
    w()
    w(f"| 指标 | 分数 | 等级 |")
    w(f"|------|------|------|")
    w(f"| 音高准确率 | {audio['pitch_score']} / 100 | {score_label(audio['pitch_score'])} |")
    w(f"| 节奏准确率 | {audio['tempo_score']} / 100 | {score_label(audio['tempo_score'])} |")
    w(f"| **综合音频分** | **{audio['overall_audio_score']} / 100** | {score_label(audio['overall_audio_score'])} |")
    w()

    w("### 2.4 节奏分析")
    w()
    tempo = audio['tempo']
    w(f"| 指标 | 数值 |")
    w(f"|------|------|")
    w(f"| 标准曲速 | {tempo['standard_tempo_bpm']} BPM |")
    w(f"| 实际弹奏速度 | {tempo['transcribed_tempo_bpm']} BPM |")
    w(f"| 速度比 | {tempo['tempo_ratio']} |")
    tempo_diff = abs(tempo['standard_tempo_bpm'] - tempo['transcribed_tempo_bpm'])
    w(f"| 速度偏差 | {tempo_diff:.1f} BPM |")
    w()

    # Pitch error examples
    pe_detail = audio.get('pitch_errors_detail', [])
    if pe_detail:
        w("### 2.5 错音示例（前 15 个）")
        w()
        w(f"| 时间 | 标准音 | 实际弹奏 | 偏差 |")
        w(f"|------|--------|----------|------|")
        for pe in pe_detail[:15]:
            w(f"| {pe['std_start']:.2f}s | {pe['expected_name']} ({pe['expected_pitch']}) | {pe['played_name']} ({pe['played_pitch']}) | {pe['pitch_diff']}半音 |")
        w()

    # Missing notes
    mn_detail = audio.get('missing_notes_detail', [])
    if mn_detail:
        w("### 2.6 漏音示例（前 15 个）")
        w()
        w(f"| 时间 | 音名 | 音高 |")
        w(f"|------|------|------|")
        for mn in mn_detail[:15]:
            w(f"| {mn['start']:.2f}s | {mn['note_name']} | {mn['pitch']} |")
        w()

    # Extra notes
    en_detail = audio.get('extra_notes_detail', [])
    if en_detail:
        w("### 2.7 多余音示例（前 15 个）")
        w()
        w(f"| 时间 | 音名 | 音高 |")
        w(f"|------|------|------|")
        for en in en_detail[:15]:
            w(f"| {en['start']:.2f}s | {en['note_name']} | {en['pitch']} |")
        w()

    # ===== Section 3: Recommendations =====
    w("---")
    w()
    w("## 三、练习建议")
    w()

    # Hand advice
    ibt = hand.get('issues_by_type', {})
    if ibt.get('folded_finger', 0) > 0:
        w(f"- **折指（{ibt['folded_finger']}次）**：手指第一关节（PIP）过度弯曲。建议进行「高抬指」练习——每根手指单独抬起、垂直落下，保持掌关节支撑。可用硬币放在手背上练习，硬币不掉说明手型稳定。")
    if ibt.get('collapsed_knuckle', 0) > 0:
        w(f"- **掌关节塌陷（{ibt['collapsed_knuckle']}次）**：手掌支撑不足。练习「握球手型」——想象手心握乒乓球，保持手指自然弯曲弧度。弹奏时手腕与前臂保持一条直线。")
    if ibt.get('over_extended', 0) > 0:
        w(f"- **手指过度伸直（{ibt['over_extended']}次）**：缺乏自然弯曲弧度。弹琴时手指应保持自然弧度（像握鼠标的手型），避免指关节锁死。可对着镜子慢练，检查手指弧度。")
    if ibt.get('thumb_tucked', 0) > 0:
        w(f"- **拇指内扣（{ibt['thumb_tucked']}次）**：拇指应保持自然外展，与食指形成C形。练习音阶时特别注意拇指穿越后的位置。")

    w()
    if audio['tempo_score'] >= 90:
        w(f"- **节奏（{audio['tempo_score']}/100）**：优秀！速度稳定，与标准曲速高度一致（偏差仅 {tempo_diff:.1f} BPM）。")
    elif audio['tempo_score'] >= 75:
        w(f"- **节奏（{audio['tempo_score']}/100）**：基本稳定，偶尔有速度波动。建议使用节拍器辅助练习。")
    else:
        w(f"- **节奏（{audio['tempo_score']}/100）**：需要加强。建议从慢速开始（50-60% 原速），用节拍器逐步提速。")

    if audio['pitch_score'] < 50:
        w(f"- **音准（{audio['pitch_score']}/100）**：当前匹配度较低。建议：")
        w(f"  - 分手慢练，确保每个音弹正确后再合手")
        w(f"  - 对照曲谱逐小节检查，找出具体错音位置")
        w(f"  - 录音后回听，与标准录音/节拍器对比")

    w()
    w("---")
    w()
    w(f"| 维度 | 手型 | 音准 | 节奏 | 综合 |")
    w(f"|------|------|------|------|------|")
    w(f"| **分数** | {hand_score} | {audio['pitch_score']} | {audio['tempo_score']} | **{overall}** |")
    w(f"| **等级** | {score_label(hand_score)} | {score_label(audio['pitch_score'])} | {score_label(audio['tempo_score'])} | **{score_label(overall)}** |")
    w()
    w("*报告由 AI 琴伴综合评估系统自动生成*")

    # Write report
    report = '\n'.join(lines)
    os.makedirs(os.path.dirname(OUTPUT_REPORT), exist_ok=True)
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)

    # Stats
    file_size = os.path.getsize(OUTPUT_REPORT)
    print(f"\nReport saved: {OUTPUT_REPORT}")
    print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"  Hand score: {hand_score}/100")
    print(f"  Audio score: {audio_score}/100")
    print(f"  Overall: {overall}/100")
    print(f"  Embedded images: {len(worst5_images_b64)}")
    print("Done!")


if __name__ == '__main__':
    main()
