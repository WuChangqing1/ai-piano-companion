import 'dart:async';
import 'dart:math' as math;
import 'package:audioplayers/audioplayers.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../models/report.dart';
import '../widgets/avatar_2d.dart';

class FeedbackScreen extends StatefulWidget {
  final EvaluateResult result;
  const FeedbackScreen({super.key, required this.result});

  @override
  State<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends State<FeedbackScreen>
    with TickerProviderStateMixin {
  final AudioPlayer _player = AudioPlayer();
  StreamSubscription? _audioSubscription;
  bool _speaking = false;

  // Animation controllers
  late AnimationController _scoreController;
  late AnimationController _fadeController;
  late AnimationController _typewriterController;
  late Animation<double> _scoreAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();

    // Score gauge animation (0 -> target score over 1.5s)
    _scoreController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _scoreAnimation = CurvedAnimation(
      parent: _scoreController,
      curve: Curves.easeOutCubic,
    );

    // Fade-in for cards
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 800),
      vsync: this,
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    );

    // Typewriter for comment
    _typewriterController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );

    // Start animations with delays
    _scoreController.forward();
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _fadeController.forward();
    });
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) _typewriterController.forward();
    });

    _play();
  }

  Future<void> _play() async {
    _audioSubscription?.cancel();
    _audioSubscription = _player.onPlayerComplete.listen((_) {
      if (mounted) setState(() => _speaking = false);
    });
    try {
      await _player.play(UrlSource(widget.result.audioUrl));
      if (mounted) setState(() => _speaking = true);
    } catch (_) {
      // Audio failure doesn't affect report viewing
    }
  }

  @override
  void dispose() {
    _audioSubscription?.cancel();
    _player.dispose();
    _scoreController.dispose();
    _fadeController.dispose();
    _typewriterController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final r = widget.result.report;
    return Scaffold(
      backgroundColor: const Color(0xFFF5F3FF),
      body: CustomScrollView(
        slivers: [
          // Hero header with gradient
          SliverToBoxAdapter(
            child: Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Color(0xFF8B5CF6), // Purple
                    Color(0xFF6366F1), // Indigo
                  ],
                ),
              ),
              child: SafeArea(
                bottom: false,
                child: Column(
                  children: [
                    // Top bar
                    Padding(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 12),
                      child: Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.arrow_back_ios,
                                color: Colors.white),
                            onPressed: () => Navigator.pop(context),
                          ),
                          const Text(
                            '练习反馈',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const Spacer(),
                          IconButton(
                            icon: const Icon(Icons.share, color: Colors.white),
                            onPressed: () {
                              // TODO: Share report
                            },
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Avatar
                    Avatar2D(speaking: _speaking, size: 120),
                    const SizedBox(height: 16),
                    // Replay button
                    Container(
                      margin: const EdgeInsets.only(bottom: 24),
                      child: TextButton.icon(
                        onPressed: _play,
                        icon: const Icon(Icons.volume_up,
                            color: Colors.white, size: 18),
                        label: const Text('再听一遍',
                            style: TextStyle(color: Colors.white)),
                        style: TextButton.styleFrom(
                          backgroundColor: Colors.white.withOpacity(0.15),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 20, vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),

          // Content
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // Score gauge card
                AnimatedBuilder(
                  animation: _scoreAnimation,
                  builder: (context, child) {
                    return _ScoreGaugeCard(
                      score: r.overallScore,
                      animationValue: _scoreAnimation.value,
                      duration: r.durationSeconds,
                    );
                  },
                ),
                const SizedBox(height: 16),

                // Comment card with typewriter
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: SlideTransition(
                    position: Tween<Offset>(
                      begin: const Offset(0, 0.2),
                      end: Offset.zero,
                    ).animate(_fadeAnimation),
                    child: _CommentCard(
                      text: r.teacherComment,
                      controller: _typewriterController,
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Radar chart card
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _RadarChartCard(report: r),
                ),
                const SizedBox(height: 16),

                // Metric cards
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _MetricCardsGrid(report: r),
                ),
                const SizedBox(height: 16),

                // Hand issues
                if (r.handIssues.isNotEmpty)
                  FadeTransition(
                    opacity: _fadeAnimation,
                    child: _IssuesCard(
                      title: '手型问题',
                      icon: Icons.pan_tool,
                      iconColor: const Color(0xFFF97316),
                      issues: r.handIssues
                          .map((i) => _IssueItem(
                                measure: i.measure,
                                timestamp: i.timestamp,
                                description: i.description,
                              ))
                          .toList(),
                    ),
                  ),
                if (r.handIssues.isNotEmpty) const SizedBox(height: 16),

                // Audio issues
                if (r.audioIssues.isNotEmpty)
                  FadeTransition(
                    opacity: _fadeAnimation,
                    child: _IssuesCard(
                      title: '音准问题',
                      icon: Icons.music_note,
                      iconColor: const Color(0xFF8B5CF6),
                      issues: r.audioIssues
                          .map((i) => _IssueItem(
                                measure: i.measure,
                                timestamp: i.timestamp,
                                description: i.issueType == 'missing_note'
                                    ? '漏弹 ${i.expected ?? '?'}'
                                    : '应为 ${i.expected ?? '?'},弹成了 ${i.actual ?? '?'}',
                              ))
                          .toList(),
                    ),
                  ),
                const SizedBox(height: 32),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

// === Score Gauge Card ===
class _ScoreGaugeCard extends StatelessWidget {
  final int score;
  final double animationValue;
  final double duration;

  const _ScoreGaugeCard({
    required this.score,
    required this.animationValue,
    required this.duration,
  });

  Color get _scoreColor {
    if (score >= 90) return const Color(0xFF10B981); // Green
    if (score >= 75) return const Color(0xFFF59E0B); // Amber
    return const Color(0xFFEF4444); // Red
  }

  @override
  Widget build(BuildContext context) {
    final animatedScore = (score * animationValue).round();
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Circular gauge
          SizedBox(
            width: 180,
            height: 180,
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Background circle
                CustomPaint(
                  size: const Size(180, 180),
                  painter: _GaugeBackgroundPainter(),
                ),
                // Animated progress
                CustomPaint(
                  size: const Size(180, 180),
                  painter: _GaugeProgressPainter(
                    progress: animationValue * (score / 100),
                    color: _scoreColor,
                  ),
                ),
                // Score text
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '$animatedScore',
                      style: TextStyle(
                        fontSize: 56,
                        fontWeight: FontWeight.bold,
                        color: _scoreColor,
                        height: 1,
                      ),
                    ),
                    const Text(
                      '综合评分',
                      style: TextStyle(
                        fontSize: 14,
                        color: Color(0xFF6B7280),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // Duration
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFF5F3FF),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.schedule,
                    size: 16, color: Color(0xFF8B5CF6)),
                const SizedBox(width: 6),
                Text(
                  '练习时长 ${duration.toStringAsFixed(0)} 秒',
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF6B7280),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _GaugeBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 12;
    final paint = Paint()
      ..color = const Color(0xFFE5E7EB)
      ..strokeWidth = 12
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawCircle(center, radius, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _GaugeProgressPainter extends CustomPainter {
  final double progress;
  final Color color;

  _GaugeProgressPainter({required this.progress, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 12;
    final paint = Paint()
      ..shader = LinearGradient(
        colors: [color, color.withOpacity(0.7)],
      ).createShader(Rect.fromCircle(center: center, radius: radius))
      ..strokeWidth = 12
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final sweepAngle = 2 * math.pi * progress;
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2, // Start from top
      sweepAngle,
      false,
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant _GaugeProgressPainter old) =>
      old.progress != progress || old.color != color;
}

// === Comment Card ===
class _CommentCard extends StatelessWidget {
  final String text;
  final AnimationController controller;

  const _CommentCard({required this.text, required this.controller});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            const Color(0xFFFFFBEB),
            const Color(0xFFFFF7ED),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFFED7AA)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFFB923C),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.format_quote,
                    color: Colors.white, size: 18),
              ),
              const SizedBox(width: 12),
              const Text(
                '老师的话',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF92400E),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          AnimatedBuilder(
            animation: controller,
            builder: (context, child) {
              final visibleLength = (text.length * controller.value).round();
              final visibleText = text.substring(0, visibleLength);
              return Text(
                visibleText,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.8,
                  color: Color(0xFF78350F),
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}

// === Radar Chart Card ===
class _RadarChartCard extends StatelessWidget {
  final PracticeReport report;

  const _RadarChartCard({required this.report});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '能力雷达图',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Color(0xFF1F2937),
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 240,
            child: RadarChart(
              RadarChartData(
                radarBackgroundColor: Colors.transparent,
                borderData: FlBorderData(show: false),
                radarBorderData: BorderSide(
                  color: const Color(0xFFE5E7EB),
                  width: 1,
                ),
                titlePositionPercentageOffset: 0.2,
                titleTextStyle: const TextStyle(
                  fontSize: 13,
                  color: Color(0xFF6B7280),
                  fontWeight: FontWeight.w500,
                ),
                getTitle: (index, angle) {
                  final titles = ['节奏', '音准', '流畅度', '手型'];
                  return RadarChartTitle(text: titles[index]);
                },
                tickCount: 4,
                ticksTextStyle: const TextStyle(
                  color: Color(0xFF9CA3AF),
                  fontSize: 10,
                ),
                tickBorderData: BorderSide(
                  color: const Color(0xFFE5E7EB),
                  width: 1,
                ),
                gridBorderData: BorderSide(
                  color: const Color(0xFFE5E7EB),
                  width: 1,
                ),
                dataSets: [
                  RadarDataSet(
                    fillColor: const Color(0xFF8B5CF6).withOpacity(0.2),
                    borderColor: const Color(0xFF8B5CF6),
                    borderWidth: 2,
                    entryRadius: 3,
                    dataEntries: [
                      RadarEntry(value: report.rhythmScore.toDouble()),
                      RadarEntry(value: report.accuracyScore.toDouble()),
                      RadarEntry(value: report.fluencyScore.toDouble()),
                      RadarEntry(value: report.handHealthScore.toDouble()),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// === Metric Cards Grid ===
class _MetricCardsGrid extends StatelessWidget {
  final PracticeReport report;

  const _MetricCardsGrid({required this.report});

  @override
  Widget build(BuildContext context) {
    final items = [
      ('节奏稳定', report.rhythmScore, Icons.graphic_eq, const Color(0xFF3B82F6)),
      ('音准准确', report.accuracyScore, Icons.tune, const Color(0xFF10B981)),
      ('流畅度', report.fluencyScore, Icons.waves, const Color(0xFFF59E0B)),
      ('手型健康', report.handHealthScore, Icons.pan_tool, const Color(0xFF8B5CF6)),
    ];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: items.map((item) => _MetricCard(
        label: item.$1,
        score: item.$2,
        icon: item.$3,
        color: item.$4,
      )).toList(),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final int score;
  final IconData icon;
  final Color color;

  const _MetricCard({
    required this.label,
    required this.score,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.1),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(height: 12),
          Text(
            label,
            style: const TextStyle(
              fontSize: 13,
              color: Color(0xFF6B7280),
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$score',
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

// === Issues Card ===
class _IssueItem {
  final int measure;
  final double timestamp;
  final String description;

  _IssueItem({
    required this.measure,
    required this.timestamp,
    required this.description,
  });
}

class _IssuesCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color iconColor;
  final List<_IssueItem> issues;

  const _IssuesCard({
    required this.title,
    required this.icon,
    required this.iconColor,
    required this.issues,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: iconColor, size: 20),
              ),
              const SizedBox(width: 12),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1F2937),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${issues.length} 处',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: iconColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...issues.map((item) => _IssueTile(
            measure: item.measure,
            timestamp: item.timestamp,
            description: item.description,
            iconColor: iconColor,
          )),
        ],
      ),
    );
  }
}

class _IssueTile extends StatelessWidget {
  final int measure;
  final double timestamp;
  final String description;
  final Color iconColor;

  const _IssueTile({
    required this.measure,
    required this.timestamp,
    required this.description,
    required this.iconColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(
              child: Text(
                '${measure}',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: iconColor,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '第 $measure 小节',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1F2937),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  description,
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF6B7280),
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFE5E7EB),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              '${timestamp.toStringAsFixed(1)}s',
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: Color(0xFF6B7280),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
