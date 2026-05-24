import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import 'practice_screen.dart';
import 'settings_screen.dart';
import 'reports_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  String? _scoreId;
  String _scoreName = '尚未上传';
  bool _uploading = false;

  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    );
    _fadeController.forward();
  }

  @override
  void dispose() {
    _fadeController.dispose();
    super.dispose();
  }

  Future<void> _pickAndUploadScore() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['jpg', 'jpeg', 'png', 'pdf'],
    );
    if (result == null || result.files.single.path == null) return;
    setState(() => _uploading = true);
    try {
      final res = await ApiClient.instance.uploadScore(
        result.files.single.path!,
        title: result.files.single.name,
      );
      setState(() {
        _scoreId = res['score_id'] as String?;
        _scoreName = result.files.single.name;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('曲谱解析成功: $_scoreName'),
          backgroundColor: const Color(0xFF10B981),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('上传失败: $e'),
          backgroundColor: const Color(0xFFEF4444),
        ),
      );
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  void _startPractice() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => PracticeScreen(scoreId: _scoreId),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
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
                    Color(0xFF8B5CF6),
                    Color(0xFF6366F1),
                  ],
                ),
              ),
              child: SafeArea(
                bottom: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Top bar
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'AI 琴伴',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 24,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Row(
                            children: [
                              _IconButton(
                                icon: Icons.bar_chart_rounded,
                                onPressed: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(builder: (_) => const ReportsScreen()),
                                ),
                              ),
                              const SizedBox(width: 8),
                              _IconButton(
                                icon: Icons.settings_rounded,
                                onPressed: () => Navigator.push(
                                  context,
                                  MaterialPageRoute(builder: (_) => const SettingsScreen()),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      // Welcome message
                      const Text(
                        '今天也要加油练琴哦',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '让 AI 老师陪你一起进步',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.8),
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Content
          SliverPadding(
            padding: const EdgeInsets.all(16),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                // Current score card
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _ScoreCard(
                    scoreName: _scoreName,
                    hasScore: _scoreId != null,
                  ),
                ),
                const SizedBox(height: 16),

                // Upload button
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _ActionButton(
                    icon: Icons.upload_file_rounded,
                    label: _uploading ? '上传中…' : '上传曲谱',
                    color: const Color(0xFF3B82F6),
                    onPressed: _uploading ? null : _pickAndUploadScore,
                  ),
                ),
                const SizedBox(height: 12),

                // Start practice button
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: _ActionButton(
                    icon: Icons.play_circle_filled_rounded,
                    label: '开始练习',
                    color: const Color(0xFF8B5CF6),
                    onPressed: _startPractice,
                    isPrimary: true,
                  ),
                ),
                const SizedBox(height: 32),

                // Tips card
                FadeTransition(
                  opacity: _fadeAnimation,
                  child: Container(
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
                                color: const Color(0xFFFEF3C7),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Icon(
                                Icons.lightbulb_outline_rounded,
                                color: Color(0xFFF59E0B),
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            const Text(
                              '小贴士',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF1F2937),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        _TipRow(
                          icon: Icons.videocam_rounded,
                          text: '把手机后置摄像头对准琴键',
                        ),
                        const SizedBox(height: 12),
                        _TipRow(
                          icon: Icons.wb_sunny_rounded,
                          text: '保持充足的光线，让 AI 看清你的手型',
                        ),
                        const SizedBox(height: 12),
                        _TipRow(
                          icon: Icons.music_note_rounded,
                          text: '弹奏完整首曲子后再停止录制',
                        ),
                      ],
                    ),
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

// === Icon Button ===
class _IconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;

  const _IconButton({required this.icon, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: IconButton(
        icon: Icon(icon, color: Colors.white),
        onPressed: onPressed,
      ),
    );
  }
}

// === Score Card ===
class _ScoreCard extends StatelessWidget {
  final String scoreName;
  final bool hasScore;

  const _ScoreCard({required this.scoreName, required this.hasScore});

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
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: hasScore
                    ? [const Color(0xFF8B5CF6), const Color(0xFF6366F1)]
                    : [const Color(0xFFE5E7EB), const Color(0xFFD1D5DB)],
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              hasScore ? Icons.music_note_rounded : Icons.add_rounded,
              color: Colors.white,
              size: 28,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '当前曲谱',
                  style: TextStyle(
                    fontSize: 12,
                    color: const Color(0xFF6B7280),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  scoreName,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1F2937),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          if (hasScore)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFDCFCE7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                '已上传',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF16A34A),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// === Action Button ===
class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback? onPressed;
  final bool isPrimary;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.color,
    this.onPressed,
    this.isPrimary = false,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: isPrimary ? color : Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: isPrimary
                    ? color.withOpacity(0.3)
                    : Colors.black.withOpacity(0.05),
                blurRadius: 20,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                color: isPrimary ? Colors.white : color,
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                label,
                style: TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w600,
                  color: isPrimary ? Colors.white : color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// === Tip Row ===
class _TipRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _TipRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 18,
          color: const Color(0xFF6B7280),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 14,
              color: Color(0xFF6B7280),
              height: 1.4,
            ),
          ),
        ),
      ],
    );
  }
}
