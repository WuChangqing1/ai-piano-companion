import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'recorder.dart';

class MobileRecorder implements PlatformRecorder {
  CameraController? _controller;

  @override
  Future<void> initialize() async {
    final cam = await Permission.camera.request();
    final mic = await Permission.microphone.request();
    if (!cam.isGranted || !mic.isGranted) {
      throw Exception('Camera/microphone permission denied');
    }
    final cameras = await availableCameras();
    if (cameras.isEmpty) throw Exception('No cameras available');
    final back = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.back,
      orElse: () => cameras.first,
    );
    _controller = CameraController(
      back,
      ResolutionPreset.high,
      enableAudio: true,
    );
    await _controller!.initialize();
  }

  @override
  Future<void> startRecording() async {
    await _controller?.startVideoRecording();
  }

  @override
  Future<String?> stopRecording() async {
    final file = await _controller?.stopVideoRecording();
    return file?.path;
  }

  @override
  void dispose() {
    _controller?.dispose();
  }

  CameraController? get cameraController => _controller;
}

PlatformRecorder getRecorder() => MobileRecorder();
Future<List<dynamic>> getAvailableCameras() async {
  try {
    return await availableCameras();
  } catch (_) {
    return [];
  }
}
