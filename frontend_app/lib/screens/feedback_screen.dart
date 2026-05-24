import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';

import '../models/report.dart';
import '../widgets/avatar_2d.dart';

class FeedbackScreen extends StatefulWidget {
  final EvaluateResult result;
  const FeedbackScreen({super.key, required this.result});

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen> {
  final AudioPlayer _player = AudioPlayer();
  bool _speaking = false;

  @override
  void initState() {
    super.initState();
    _play();
  }

  Future<void> _play() async {
    _player.onPlayerComplete.listen((_) {
      if (mounted) setState(() => _speaking = false);
    });
    try {
      await _player.play(UrlSource(widget.result.audioUrl));
      if (mounted) setState(() => _speaking = true);
    } catch (_) {
      // 音频失败不影响报告查看
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.result.report;
    return Scaffold(
      appBar: AppBar(title: const Text('练习反馈')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(child: Avatar2D(speaking: _speaking, size: 180)),
          const SizedBox(height: 12),
          Center(
            child: TextButton.icon(
              onPressed: _play,
              icon: const Icon(Icons.volume_up),
              label: const Text('再听一遍'),
            ),
          ),
          const SizedBox(height: 16),
          _CommentCard(text: r.teacherComment),
          const SizedBox(height: 16),
          _ScoreRow(report: r),
          const SizedBox(height: 16),
          _MetricCards(report: r),
          const SizedBox(height: 16),
          _HandIssuesCard(issues: r.handIssues),
          const SizedBox(height: 16),
          _AudioIssuesCard(issues: r.audioIssues),
        ],
      ),
    );
  }
}

class _CommentCard extends StatelessWidget {
  final String text;
  const _CommentCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF7E6),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFFD591)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.format_quote, color: Color(0xFFFA8C16)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(text,
                style: const TextStyle(fontSize: 15, height: 1.6)),
          ),
        ],
      ),
    );
  }
}

class _ScoreRow extends StatelessWidget {
  final PracticeReport report;
  const _ScoreRow({required this.report});

  @override
  Widget build(BuildContext context) {
    Color color;
    if (report.overallScore >= 90) {
      color = Colors.green;
    } else if (report.overallScore >= 75) {
      color = Colors.orange;
    } else {
      color = Colors.redAccent;
    }
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Text('${report.overallScore}',
              style: TextStyle(
                  fontSize: 56,
                  fontWeight: FontWeight.bold,
                  color: color)),
          const SizedBox(width: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('综合评分',
                  style: TextStyle(fontSize: 14, color: Colors.black54)),
              const SizedBox(height: 4),
              Text('练习时长 ${report.durationSeconds.toStringAsFixed(0)} 秒',
                  style: const TextStyle(fontSize: 13)),
            ],
          ),
        ],
      ),
    );
  }
}

class _MetricCards extends StatelessWidget {
  final PracticeReport report;
  const _MetricCards({required this.report});

  @override
  Widget build(BuildContext context) {
    final items = [
      ('节奏稳定', report.rhythmScore),
      ('音准准确', report.accuracyScore),
      ('流畅度', report.fluencyScore),
      ('手型健康', report.handHealthScore),
    ];
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 2.4,
      children: items
          .map((e) => Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.black12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(e.$1,
                        style: const TextStyle(
                            color: Colors.black54, fontSize: 13)),
                    const SizedBox(height: 6),
                    Text('${e.$2}',
                        style: const TextStyle(
                            fontSize: 22, fontWeight: FontWeight.w600)),
                  ],
                ),
              ))
          .toList(),
    );
  }
}

class _HandIssuesCard extends StatelessWidget {
  final List<HandIssue> issues;
  const _HandIssuesCard({required this.issues});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.black12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('手型问题',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
          const SizedBox(height: 8),
          if (issues.isEmpty)
            const Text('没有发现明显手型问题,棒!',
                style: TextStyle(color: Colors.black54)),
          ...issues.map((i) => ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.pan_tool, color: Colors.deepOrange),
                title: Text('第 ${i.measure} 小节'),
                subtitle: Text(i.description),
                trailing: Text('${i.timestamp.toStringAsFixed(1)}s'),
              )),
        ],
      ),
    );
  }
}

class _AudioIssuesCard extends StatelessWidget {
  final List<AudioIssue> issues;
  const _AudioIssuesCard({required this.issues});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.black12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('音准问题',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
          const SizedBox(height: 8),
          if (issues.isEmpty)
            const Text('所有音符都很准,继续保持!',
                style: TextStyle(color: Colors.black54)),
          ...issues.map((i) {
            final desc = i.issueType == 'missing_note'
                ? '漏弹 ${i.expected ?? '?'}'
                : '应为 ${i.expected ?? '?'},弹成了 ${i.actual ?? '?'}';
            return ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.music_note, color: Colors.purple),
              title: Text('第 ${i.measure} 小节'),
              subtitle: Text(desc),
              trailing: Text('${i.timestamp.toStringAsFixed(1)}s'),
            );
          }),
        ],
      ),
    );
  }
}
