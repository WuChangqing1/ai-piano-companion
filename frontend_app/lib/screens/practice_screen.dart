import 'dart:async';
import 'dart:math' as math;
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../services/api_client.dart';
import 'feedback_screen.dart';

class PracticeScreen extends StatefulWidget {
  final String? scoreId;
  const PracticeScreen({super.key, this.scoreId});

  @override
  State<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends State<PracticeScreen>
    with TickerProviderStateMixin {
  CameraController? _controller;
  bool _initializing = true;
  bool _recording = false;
  bool _uploading = false;
  String? _error;

  // Countdown animation
  late AnimationController _countdownController;
  late Animation<int> _countdownAnimation;
  bool _showCountdown = false;

  // Recording timer
  Timer? _timer;
  int _elapsedSeconds = 0;

  // Stop button pulse animation
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();

    _countdownController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    );
    _countdownAnimation = IntTween(begin: 3, end: 0).animate(
      CurvedAnimation(parent: _countdownController, curve: Curves.linear),
    );

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
    final cam = await Permission.camera.request();
    final mic = await Permission.microphone.request();
    if (!cam.isGranted || !mic.isGranted) {
      setState(() {
        _initializing = false;
        _error = '需要授予相机与麦克风权限才能开始练习';
      });
      return;
    }
    try {
      final cameras = await availableCameras();
      final back = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      final controller = CameraController(
        back,
        ResolutionPreset.high,
        enableAudio: true,
      );
      await controller.initialize();

      if (!mounted) return;
      setState(() {
        _controller = controller;
        _initializing = false;
        _showCountdown = true;
      });

      // Start countdown
      _countdownController.forward().then((_) async {
        if (!mounted) return;
        setState(() => _showCountdown = false);
        await controller.startVideoRecording();
        if (!mounted) return;
        setState(() => _recording = true);
        _startTimer();
      });
    } catch (e) {
      setState(() {
        _initializing = false;
        _error = '相机初始化失败: $e';
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
    if (_controller == null || !_recording) return;
    _timer?.cancel();
    setState(() => _uploading = true);
    try {
      final file = await _controller!.stopVideoRecording();
      _recording = false;
      final result = await ApiClient.instance.evaluate(
        file.path,
        scoreId: widget.scoreId,
      );
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

  @override
  void dispose() {
    _timer?.cancel();
    _countdownController.dispose();
    _pulseController.dispose();
    _controller?.dispose();
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
                '正在初始化相机...',
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
                Icon(Icons.error_outline, color: Colors.red.shade300, size: 64),
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
          // Camera preview
          if (_controller != null)
            Positioned.fill(child: CameraPreview(_controller!)),

          // Countdown overlay
          if (_showCountdown)
            Positioned.fill(
              child: Container(
                color: Colors.black.withOpacity(0.5),
                child: AnimatedBuilder(
                  animation: _countdownAnimation,
                  builder: (context, child) {
                    return Center(
                      child: Text(
                        '${_countdownAnimation.value}',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 120,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),

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
          // Wave animation
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
      final height = (math.sin(phase) * 0.5 + 0.5) * size.height * 0.8 + 4;
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
