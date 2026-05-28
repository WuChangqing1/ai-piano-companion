"""Generate HTML comprehensive report for any test directory.
Usage: python generate_html_report.py [test_dir_name]  (default: test2)
Example: python generate_html_report.py test3
"""
import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path

PARENT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_data')
TEST_NAME = sys.argv[1] if len(sys.argv) > 1 else 'test2'
TEST_DIR = os.path.join(PARENT_DIR, TEST_NAME)
HAND_JSON = os.path.join(TEST_DIR, 'hand_analysis_report', 'hand_analysis_data.json')
AUDIO_JSON = os.path.join(TEST_DIR, 'audio_comparison.json')
REPORT_DIR = os.path.join(TEST_DIR, 'hand_analysis_report')
OUTPUT_HTML = os.path.join(TEST_DIR, 'COMPREHENSIVE_REPORT.html')


def img_to_base64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode('ascii')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def score_color(score):
    if score >= 90: return '#22c55e'
    if score >= 75: return '#3b82f6'
    if score >= 60: return '#f59e0b'
    return '#ef4444'


def score_label(score):
    if score >= 90: return '优秀'
    if score >= 75: return '良好'
    if score >= 60: return '及格'
    return '需要加强'


def severity_badge(issue_type):
    if issue_type in ('folded_finger', 'collapsed_knuckle'):
        return '<span class="badge badge-danger">严重</span>'
    return '<span class="badge badge-warning">轻度</span>'


def issue_type_name(t):
    names = {
        'folded_finger': '折指（PIP关节过度弯曲）',
        'collapsed_knuckle': '掌关节塌陷（MCP低于PIP）',
        'over_extended': '手指过度伸直',
        'thumb_tucked': '拇指内扣',
    }
    return names.get(t, t)


def main():
    print(f"Generating HTML report for {TEST_NAME}...")

    hand = load_json(HAND_JSON)
    audio = load_json(AUDIO_JSON)

    hand_score = round(hand['avg_score'])
    audio_score = audio['overall_audio_score']
    overall = round(hand_score * 0.5 + audio_score * 0.5)

    # Encode worst_5 images
    print("Encoding images...")
    worst5_b64 = []
    worst5_data = hand.get('worst_5', [])
    for wf in worst5_data:
        img_rel = wf.get('worst_image_path', '')
        if img_rel:
            img_path = os.path.join(REPORT_DIR, img_rel)
            if os.path.exists(img_path):
                worst5_b64.append(img_to_base64(img_path))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI 琴伴 - 综合评估报告</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f0f2f5; color: #1a1a2e; line-height: 1.6;
}}
.container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}

.header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; border-radius: 16px; padding: 32px 28px; margin-bottom: 20px;
    text-align: center;
}}
.header h1 {{ font-size: 26px; font-weight: 700; margin-bottom: 8px; }}
.header .subtitle {{ font-size: 13px; opacity: 0.85; }}

.score-row {{ display: flex; gap: 12px; margin-bottom: 20px; }}
.score-card {{
    flex: 1; background: white; border-radius: 14px; padding: 20px;
    text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}
.score-card .label {{ font-size: 13px; color: #6b7280; margin-bottom: 8px; }}
.score-card .value {{ font-size: 36px; font-weight: 800; }}
.score-card .grade {{ font-size: 12px; margin-top: 4px; }}
.score-card .bar {{
    height: 6px; border-radius: 3px; margin-top: 10px; overflow: hidden;
    background: #e5e7eb;
}}
.score-card .bar-fill {{ height: 100%; border-radius: 3px; }}

.section {{
    background: white; border-radius: 14px; padding: 28px; margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}
.section h2 {{
    font-size: 20px; font-weight: 700; margin-bottom: 20px;
    padding-bottom: 12px; border-bottom: 2px solid #f0f0f5;
    display: flex; align-items: center; gap: 8px;
}}
.section h3 {{ font-size: 16px; font-weight: 600; margin: 24px 0 12px; color: #374151; }}
.section h4 {{ font-size: 15px; font-weight: 600; margin: 20px 0 10px; color: #4b5563; }}

table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }}
th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #f3f4f6; }}
th {{ background: #f9fafb; font-weight: 600; color: #6b7280; font-size: 13px; }}
tr:hover td {{ background: #fafbff; }}

.badge {{
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600;
}}
.badge-danger {{ background: #fee2e2; color: #dc2626; }}
.badge-warning {{ background: #fef3c7; color: #d97706; }}
.badge-success {{ background: #d1fae5; color: #059669; }}

.frame-card {{
    border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;
    margin: 16px 0; background: #fafbfc;
}}
.frame-card h4 {{ margin-top: 0; }}
.frame-card img {{ width: 100%; border-radius: 8px; margin-top: 12px; border: 1px solid #e5e7eb; }}
.frame-meta {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 13px; color: #6b7280; margin: 8px 0; }}

.advice-list {{ list-style: none; padding: 0; }}
.advice-list li {{
    padding: 10px 14px; margin: 6px 0; background: #f9fafb;
    border-left: 3px solid #667eea; border-radius: 0 8px 8px 0;
    font-size: 14px;
}}

.footer {{ text-align: center; padding: 20px; color: #9ca3af; font-size: 12px; }}

.issue-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.issue-item {{
    padding: 10px 14px; background: #f9fafb; border-radius: 8px;
    font-size: 13px; display: flex; justify-content: space-between; align-items: center;
}}
.issue-item .count {{ font-weight: 700; font-size: 16px; }}

@media (max-width: 600px) {{
    .score-row {{ flex-direction: column; }}
    .issue-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>AI 琴伴 · 综合评估报告</h1>
'''

    # Count sheet music pages
    import glob
    page_count = len(glob.glob(os.path.join(TEST_DIR, '*.jpg'))) + len(glob.glob(os.path.join(TEST_DIR, '*.png')))

    html += f'''
    <div class="subtitle">生成时间: {now} &nbsp;|&nbsp; 测试数据: {TEST_NAME} ({hand['duration_s']:.0f}s · {hand['resolution']} · {page_count}页曲谱)</div>
</div>

<div class="score-row">
    <div class="score-card">
        <div class="label">手型</div>
        <div class="value" style="color:{score_color(hand_score)}">{hand_score}</div>
        <div class="grade" style="color:{score_color(hand_score)}">{score_label(hand_score)}</div>
        <div class="bar"><div class="bar-fill" style="width:{hand_score}%;background:{score_color(hand_score)}"></div></div>
    </div>
    <div class="score-card">
        <div class="label">音频</div>
        <div class="value" style="color:{score_color(audio_score)}">{audio_score}</div>
        <div class="grade" style="color:{score_color(audio_score)}">{score_label(audio_score)}</div>
        <div class="bar"><div class="bar-fill" style="width:{audio_score}%;background:{score_color(audio_score)}"></div></div>
    </div>
    <div class="score-card">
        <div class="label">综合</div>
        <div class="value" style="color:{score_color(overall)}">{overall}</div>
        <div class="grade" style="color:{score_color(overall)}">{score_label(overall)}</div>
        <div class="bar"><div class="bar-fill" style="width:{overall}%;background:{score_color(overall)}"></div></div>
    </div>
</div>

<div class="section">
    <h2>一、手型分析</h2>

    <h3>1.1 视频概览</h3>
    <table>
        <tr><th style="width:40%">指标</th><th>数值</th></tr>
        <tr><td>视频</td><td>{hand['video']}</td></tr>
        <tr><td>视频时长</td><td>{hand['duration_s']}s</td></tr>
        <tr><td>帧率</td><td>{hand['fps']} FPS</td></tr>
        <tr><td>分辨率</td><td>{hand['resolution']}</td></tr>
        <tr><td>采样帧数</td><td>{hand['total_frames_sampled']}</td></tr>
        <tr><td>检测到手的帧数</td><td>{hand['frames_with_hands']}</td></tr>
        <tr><td>检测到手的总次数</td><td>{hand['total_hands_detected']}</td></tr>
        <tr><td>过滤非弹奏帧</td><td>{hand.get('skipped_by_filter', 0)}</td></tr>
        <tr style="font-weight:700"><td>平均手型分</td><td style="color:{score_color(hand_score)};font-size:18px">{hand_score} / 100</td></tr>
        <tr><td>最佳 / 最差帧</td><td>{hand['best_score']:.0f} / {hand['worst_score']:.0f}</td></tr>
    </table>

    <h3>1.2 问题类型分布</h3>
    <div class="issue-grid">'''

    for t, c in sorted(hand.get('issues_by_type', {}).items(), key=lambda x: -x[1]):
        html += f'''<div class="issue-item"><span>{issue_type_name(t)}</span><span class="count" style="color:{score_color(100 - c * 3)}">{c}</span></div>'''

    html += '</div><h3>1.3 问题手指分布</h3><table><tr><th>手指</th><th>问题次数</th></tr>'

    for finger, c in sorted(hand.get('issues_by_finger', {}).items(), key=lambda x: -x[1]):
        html += f'<tr><td>{finger}</td><td>{c}</td></tr>'

    html += '</table><h3>1.4 手型最差 5 帧（骨架标注）</h3><p style="color:#6b7280;font-size:13px;margin-bottom:12px">以下为 MediaPipe 21点关键点检测标注的红色骨架图，按问题严重度排序。</p>'

    for i, wf in enumerate(worst5_data):
        rank = i + 1
        s = wf['score']
        issues = wf.get('issues', [])
        img_src = f'data:image/jpeg;base64,{worst5_b64[i]}' if i < len(worst5_b64) else ''

        html += f'''
    <div class="frame-card">
        <h4>第 {rank} 名 — 得分: <span style="color:{score_color(s)}">{s:.0f} / 100</span></h4>
        <div class="frame-meta">
            <span>时间: {wf['timestamp']}s</span>
            <span>小节: 第 {wf.get('measure', '?')} 小节</span>
            <span>检测到手: {wf.get('hands_detected', 0)}</span>
            <span>问题数: {len(issues)}</span>
        </div>'''

        if issues:
            html += '<table><tr><th>手</th><th>手指</th><th>问题类型</th><th>严重度</th></tr>'
            for iss in issues:
                html += f'<tr><td>{iss.get("hand", "")}</td><td>{iss.get("finger", "")}</td><td>{issue_type_name(iss.get("type", ""))}</td><td>{severity_badge(iss.get("type", ""))}</td></tr>'
            html += '</table>'

        if img_src:
            html += f'<img src="{img_src}" alt="手型帧{rank}" loading="lazy">'
        html += '\n    </div>'

    # Audio section
    tempo = audio['tempo']
    tm = audio.get('time_matched_count', audio['correct_count'] + audio['pitch_error_count'])
    tdiff = abs(tempo['standard_tempo_bpm'] - tempo['transcribed_tempo_bpm'])

    html += f'''
</div>

<div class="section">
    <h2>二、音频分析</h2>

    <h3>2.1 数据概览</h3>
    <table>
        <tr><th style="width:40%">指标</th><th>数值</th></tr>
        <tr><td>曲谱解析方式</td><td>Oemer ONNX (OMR)</td></tr>
        <tr><td>标准曲谱音符数</td><td>{audio['standard_note_count']}</td></tr>
        <tr><td>音频转录方式</td><td>basic-pitch ONNX</td></tr>
        <tr><td>转录音符数</td><td>{audio['transcribed_note_count']}</td></tr>
        <tr><td>起始偏移（自动对齐）</td><td>{audio.get('start_offset', 0)}s</td></tr>
        <tr><td>时间匹配容差</td><td>0.5s</td></tr>
    </table>

    <h3>2.2 比对结果</h3>
    <table>
        <tr><th>类别</th><th>数量</th><th>说明</th></tr>
        <tr><td>时间匹配</td><td>{tm}</td><td>音频与曲谱在时间上对齐</td></tr>
        <tr><td><span class="badge badge-success">正确</span></td><td><b>{audio['correct_count']}</b></td><td>时间和音高完全匹配</td></tr>
        <tr><td><span class="badge badge-warning">错音</span></td><td><b>{audio['pitch_error_count']}</b></td><td>时间对上但弹了不同的音</td></tr>
        <tr><td><span class="badge badge-danger">漏音</span></td><td><b>{audio['missing_count']}</b></td><td>标准曲谱有但未弹奏</td></tr>
        <tr><td>多余音</td><td><b>{audio['extra_count']}</b></td><td>弹了但曲谱上不存在的音</td></tr>
    </table>

    <h3>2.3 音频评分</h3>
    <table>
        <tr><th>指标</th><th>分数</th><th>等级</th></tr>
        <tr><td>音高准确率</td><td style="color:{score_color(audio['pitch_score'])};font-weight:700">{audio['pitch_score']} / 100</td><td><span class="badge badge-{"success" if audio['pitch_score'] >= 90 else "warning" if audio['pitch_score'] >= 60 else "danger"}">{score_label(audio['pitch_score'])}</span></td></tr>
        <tr><td>节奏准确率</td><td style="color:{score_color(audio['tempo_score'])};font-weight:700">{audio['tempo_score']} / 100</td><td><span class="badge badge-{"success" if audio['tempo_score'] >= 90 else "warning"}">{score_label(audio['tempo_score'])}</span></td></tr>
        <tr style="font-weight:700"><td>综合音频分</td><td style="color:{score_color(audio_score)};font-size:18px">{audio_score} / 100</td><td><span class="badge badge-{"success" if audio_score >= 90 else "warning" if audio_score >= 60 else "danger"}">{score_label(audio_score)}</span></td></tr>
    </table>

    <h3>2.4 节奏分析</h3>
    <table>
        <tr><th style="width:40%">指标</th><th>数值</th></tr>
        <tr><td>标准曲速</td><td>{tempo['standard_tempo_bpm']} BPM</td></tr>
        <tr><td>实际弹奏速度</td><td>{tempo['transcribed_tempo_bpm']} BPM</td></tr>
        <tr><td>速度比</td><td>{tempo['tempo_ratio']}</td></tr>
        <tr><td>速度偏差</td><td>{tdiff:.1f} BPM</td></tr>
    </table>'''

    pe_detail = audio.get('pitch_errors_detail', [])
    if pe_detail:
        html += '<h3>2.5 错音示例（前15个）</h3><table><tr><th>时间</th><th>标准音</th><th>实际弹奏</th><th>偏差</th></tr>'
        for pe in pe_detail[:15]:
            html += f'<tr><td>{pe["std_start"]:.2f}s</td><td><b>{pe["expected_name"]}</b> ({pe["expected_pitch"]})</td><td><b>{pe["played_name"]}</b> ({pe["played_pitch"]})</td><td>{pe["pitch_diff"]}半音</td></tr>'
        html += '</table>'

    mn = audio.get('missing_notes_detail', [])
    en = audio.get('extra_notes_detail', [])
    if mn and en:
        html += '<div style="display:flex;gap:16px;flex-wrap:wrap"><div style="flex:1;min-width:280px"><h3>2.6 漏音（前15个）</h3><table><tr><th>时间</th><th>音名</th><th>音高</th></tr>'
        for m in mn[:15]:
            html += f'<tr><td>{m["start"]:.2f}s</td><td>{m["note_name"]}</td><td>{m["pitch"]}</td></tr>'
        html += '</table></div><div style="flex:1;min-width:280px"><h3>2.7 多余音（前15个）</h3><table><tr><th>时间</th><th>音名</th><th>音高</th></tr>'
        for e in en[:15]:
            html += f'<tr><td>{e["start"]:.2f}s</td><td>{e["note_name"]}</td><td>{e["pitch"]}</td></tr>'
        html += '</table></div></div>'

    # Recommendations
    ibt = hand.get('issues_by_type', {})
    html += '''
</div>

<div class="section">
    <h2>三、练习建议</h2>
    <ul class="advice-list">'''

    if ibt.get('folded_finger', 0):
        html += f'<li><b>折指（{ibt["folded_finger"]}次）</b>：手指第一关节（PIP）过度弯曲。建议「高抬指」练习——每根手指单独抬起、垂直落下，保持掌关节支撑。</li>'
    if ibt.get('collapsed_knuckle', 0):
        html += f'<li><b>掌关节塌陷（{ibt["collapsed_knuckle"]}次）</b>：手掌支撑不足。练习「握球手型」——想象手心握乒乓球，保持手指自然弯曲弧度。</li>'
    if ibt.get('over_extended', 0):
        html += f'<li><b>手指过度伸直（{ibt["over_extended"]}次）</b>：缺乏自然弯曲弧度。可对着镜子慢练，检查手指弧度。</li>'
    if ibt.get('thumb_tucked', 0):
        html += f'<li><b>拇指内扣（{ibt["thumb_tucked"]}次）</b>：拇指应自然外展，与食指形成C形。练习音阶时注意拇指穿越后的位置。</li>'

    if audio['tempo_score'] >= 90:
        html += f'<li><b>节奏（{audio["tempo_score"]}/100）</b>：优秀！速度稳定，与标准曲速偏差仅 {tdiff:.1f} BPM。</li>'
    else:
        html += f'<li><b>节奏（{audio["tempo_score"]}/100）</b>：当前与标准曲速偏差 {tdiff:.1f} BPM。建议使用节拍器从慢速开始练习。</li>'

    if audio['pitch_score'] < 50:
        html += f'<li><b>音准（{audio["pitch_score"]}/100）</b>：当前匹配度较低。建议分手慢练，对照曲谱逐小节检查。</li>'

    html += f'''
    </ul>
</div>

<div class="section" style="text-align:center">
    <h2 style="border:none;justify-content:center">评分汇总</h2>
    <table>
        <tr><th>维度</th><th>手型</th><th>音准</th><th>节奏</th><th>综合</th></tr>
        <tr>
            <td><b>分数</b></td>
            <td style="color:{score_color(hand_score)};font-weight:700;font-size:16px">{hand_score}</td>
            <td style="color:{score_color(audio['pitch_score'])};font-weight:700;font-size:16px">{audio['pitch_score']}</td>
            <td style="color:{score_color(audio['tempo_score'])};font-weight:700;font-size:16px">{audio['tempo_score']}</td>
            <td style="color:{score_color(overall)};font-weight:700;font-size:18px">{overall}</td>
        </tr>
        <tr>
            <td><b>等级</b></td>
            <td><span class="badge badge-success">{score_label(hand_score)}</span></td>
            <td><span class="badge badge-{"success" if audio["pitch_score"]>=90 else "warning" if audio["pitch_score"]>=60 else "danger"}">{score_label(audio["pitch_score"])}</span></td>
            <td><span class="badge badge-{"success" if audio["tempo_score"]>=90 else "warning"}">{score_label(audio["tempo_score"])}</span></td>
            <td><span class="badge badge-{"success" if overall>=90 else "warning" if overall>=60 else "danger"}" style="font-size:14px;padding:4px 14px">{score_label(overall)}</span></td>
        </tr>
    </table>
</div>

<div class="footer">AI 琴伴综合评估系统 · 自动生成</div>

</div>
</body>
</html>'''

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size = os.path.getsize(OUTPUT_HTML)
    print(f"Report saved: {OUTPUT_HTML}")
    print(f"  Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"  Hand: {hand_score} | Audio: {audio_score} | Overall: {overall}")
    print("Done!")


if __name__ == '__main__':
    main()
