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

class _PracticeScreenState extends State<PracticeScreen> {
  CameraController? _controller;
  bool _initializing = true;
  bool _recording = false;
  bool _uploading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
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
      await controller.startVideoRecording();
      if (!mounted) return;
      setState(() {
        _controller = controller;
        _recording = true;
        _initializing = false;
      });
    } catch (e) {
      setState(() {
        _initializing = false;
        _error = '相机初始化失败:$e';
      });
    }
  }

  Future<void> _stopAndUpload() async {
    if (_controller == null || !_recording) return;
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
        SnackBar(content: Text('上传或评估失败:$e')),
      );
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_initializing) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('练习')),
        body: Center(child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(_error!, textAlign: TextAlign.center),
        )),
      );
    }
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          if (_controller != null)
            Positioned.fill(child: CameraPreview(_controller!)),
          Positioned(
            top: 50, left: 20,
            child: SafeArea(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.8),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.fiber_manual_record,
                        color: Colors.white, size: 14),
                    SizedBox(width: 6),
                    Text('REC',
                        style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 60,
            left: 0,
            right: 0,
            child: Center(
              child: _uploading
                  ? Column(
                      children: const [
                        CircularProgressIndicator(color: Colors.white),
                        SizedBox(height: 16),
                        Text('AI 老师正在思考…',
                            style: TextStyle(color: Colors.white, fontSize: 18)),
                      ],
                    )
                  : GestureDetector(
                      onTap: _stopAndUpload,
                      child: Container(
                        width: 90,
                        height: 90,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white,
                          border: Border.all(color: Colors.red, width: 6),
                        ),
                        child: const Icon(Icons.stop,
                            color: Colors.red, size: 40),
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
