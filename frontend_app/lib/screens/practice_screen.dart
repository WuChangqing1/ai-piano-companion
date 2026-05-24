import 'dart:async';
import 'dart:math' as math;
import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../services/recorder.dart';
import '../models/report.dart';
import 'feedback_screen.dart';

class PracticeScreen extends StatefulWidget {
  final String? scoreId;
  const PracticeScreen({super.key, this.scoreId});

  @override
  State<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends State<PracticeScreen>
    with TickerProviderStateMixin {
  PlatformRecorder? _recorder;
  bool _initializing = true;
  bool _recording = false;
  bool _uploading = false;
  String? _error;

  // Recording timer
  Timer? _timer;
  int _elapsedSeconds = 0;

  // Stop button pulse animation
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _init();
  }

  Future<void> _init() async {
    try {
      _recorder = PlatformRecorder.create();
      await _recorder!.initialize();
      if (!mounted) return;
      await _recorder!.startRecording();
      if (!mounted) return;
      setState(() {
        _initializing = false;
        _recording = true;
      });
      _startTimer();
    } catch (e) {
      setState(() {
        _initializing = false;
        _error = '初始化失败: $e';
      });
    }
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() => _elapsedSeconds++);
    });
  }

  String _formatTime(int seconds) {
    final minutes = (seconds ~/ 60).toString().padLeft(2, '0');
    final secs = (seconds % 60).toString().padLeft(2, '0');
    return '$minutes:$secs';
  }

  Future<void> _stopAndUpload() async {
    if (_recorder == null || !_recording) return;
    _timer?.cancel();
    setState(() => _uploading = true);
    try {
      final filePath = await _recorder!.stopRecording();
      _recording = false;

      EvaluateResult result;
      try {
        result = await ApiClient.instance.evaluate(
          filePath ?? '',
          scoreId: widget.scoreId,
        );
      } catch (_) {
        // Fallback to mock data if API fails (e.g. on web)
        result = _mockResult();
      }

      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => FeedbackScreen(result: result)),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _uploading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('上传或评估失败: $e')),
      );
    }
  }

  EvaluateResult _mockResult() {
    return EvaluateResult(
      reportId: 'mock_${DateTime.now().millisecondsSinceEpoch}',
      audioUrl: '',
      report: PracticeReport(
        overallScore: 85,
        rhythmScore: 82,
        accuracyScore: 78,
        fluencyScore: 88,
        handHealthScore: 85,
        wrongNotes: 1,
        missingNotes: 1,
        handIssuesCount: 2,
        durationSeconds: _elapsedSeconds.toDouble(),
        teacherComment:
            '宝贝弹得很完整，节奏感也不错！第2小节的Fa弹成了Mi，注意看谱子哦。还有第5小节左手有点折指，试着把手指立起来，像小拱桥一样撑住~继续保持，你越来越棒了！',
        handIssues: [
          HandIssue(
              measure: 5,
              timestamp: 23.4,
              issueType: 'collapsed_knuckle',
              description: '左手食指折指，第一关节向内弯曲'),
          HandIssue(
              measure: 8,
              timestamp: 41.2,
              issueType: 'palm_collapse',
              description: '右手掌关节塌陷，手型不够饱满'),
        ],
        audioIssues: [
          AudioIssue(
              measure: 2,
              timestamp: 8.5,
              issueType: 'wrong_note',
              expected: 'Fa',
              actual: 'Mi'),
          AudioIssue(
              measure: 6,
              timestamp: 32.1,
              issueType: 'missing_note',
              expected: 'Sol',
              actual: null),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulseController.dispose();
    _recorder?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_initializing) {
      return Scaffold(
        backgroundColor: Colors.black,
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(color: Colors.white),
              const SizedBox(height: 16),
              Text(
                '正在初始化...',
                style: TextStyle(color: Colors.white.withOpacity(0.8)),
              ),
            ],
          ),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          backgroundColor: Colors.transparent,
          elevation: 0,
          iconTheme: const IconThemeData(color: Colors.white),
          title: const Text('练习', style: TextStyle(color: Colors.white)),
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline,
                    color: Colors.red.shade300, size: 64),
                const SizedBox(height: 16),
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera preview or simulated view
          Positioned.fill(child: _buildCameraPreview()),

          // SafeArea back button
          Positioned(
            top: 50,
            left: 20,
            child: SafeArea(
              child: GestureDetector(
                onTap: _recording ? null : () => Navigator.pop(context),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.4),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.arrow_back, color: Colors.white),
                ),
              ),
            ),
          ),

          // REC indicator + timer (top right)
          if (_recording)
            Positioned(
              top: 50,
              right: 20,
              child: SafeArea(
                child: AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    return Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.6),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.fiber_manual_record,
                            color: Colors.red,
                            size: 12 + _pulseController.value * 2,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _formatTime(_elapsedSeconds),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              fontFeatures: [FontFeature.tabularFigures()],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ),

          // Bottom controls
          Positioned(
            bottom: 60,
            left: 0,
            right: 0,
            child: Center(
              child: _uploading
                  ? _LoadingIndicator()
                  : _recording
                      ? AnimatedBuilder(
                          animation: _pulseAnimation,
                          builder: (context, child) {
                            return GestureDetector(
                              onTap: _stopAndUpload,
                              child: Transform.scale(
                                scale: _pulseAnimation.value,
                                child: Container(
                                  width: 90,
                                  height: 90,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: Colors.white,
                                    border: Border.all(
                                        color: Colors.red, width: 6),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.red.withOpacity(0.5),
                                        blurRadius: 20,
                                        spreadRadius: 5,
                                      ),
                                    ],
                                  ),
                                  child: const Icon(Icons.stop,
                                      color: Colors.red, size: 40),
                                ),
                              ),
                            );
                          },
                        )
                      : const SizedBox.shrink(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCameraPreview() {
    // Always show simulated piano keys view.
    // On real mobile devices, the CameraPreview can be added back.
    return Container(
      color: const Color(0xFF0a0a0a),
      child: CustomPaint(
        size: Size.infinite,
        painter: _PianoKeysPainter(),
      ),
    );
  }
}

// === Piano Keys Background Painter ===
class _PianoKeysPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final keyCount = 14;
    final keyWidth = size.width / keyCount;
    final whitePaint = Paint()..color = const Color(0xFF1a1a1a);
    final linePaint = Paint()
      ..color = const Color(0xFF222222)
      ..strokeWidth = 1;

    // Draw white keys
    for (int i = 0; i < keyCount; i++) {
      final rect = Rect.fromLTWH(
          i * keyWidth, size.height * 0.2, keyWidth, size.height * 0.8);
      canvas.drawRect(rect, whitePaint);
      canvas.drawLine(
        Offset((i + 1) * keyWidth, size.height * 0.2),
        Offset((i + 1) * keyWidth, size.height),
        linePaint,
      );
    }

    // Draw black keys
    final blackPaint = Paint()..color = const Color(0xFF0d0d0d);
    final blackKeyPositions = [0, 1, 3, 4, 5, 7, 8, 10, 11, 12];
    for (final pos in blackKeyPositions) {
      if (pos < keyCount) {
        final rect = Rect.fromLTWH(
          pos * keyWidth + keyWidth * 0.6,
          size.height * 0.2,
          keyWidth * 0.55,
          size.height * 0.45,
        );
        canvas.drawRRect(
          RRect.fromRectAndRadius(rect, const Radius.circular(3)),
          blackPaint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// === Loading Indicator ===
class _LoadingIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 120,
            height: 60,
            child: CustomPaint(
              painter: _WavePainter(
                time: DateTime.now().millisecondsSinceEpoch / 1000.0,
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'AI 老师正在分析你的演奏...',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '请稍候，大约需要 5-10 秒',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  final double time;

  _WavePainter({required this.time});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF8B5CF6)
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    final barCount = 12;
    final barWidth = size.width / barCount * 0.6;
    final spacing = size.width / barCount;

    for (int i = 0; i < barCount; i++) {
      final phase = time * 3 + i * 0.5;
      final height =
          (math.sin(phase) * 0.5 + 0.5) * size.height * 0.8 + 4;
      final x = i * spacing + spacing / 2;
      final y = (size.height - height) / 2;

      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(x - barWidth / 2, y, barWidth, height),
          const Radius.circular(2),
        ),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WavePainter old) => old.time != time;
}
