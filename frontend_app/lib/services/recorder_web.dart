import 'recorder.dart';

class WebRecorder implements PlatformRecorder {
  @override
  Future<void> initialize() async {
    await Future.delayed(const Duration(milliseconds: 500));
  }

  @override
  Future<void> startRecording() async {}

  @override
  Future<String?> stopRecording() async {
    await Future.delayed(const Duration(milliseconds: 300));
    return 'web_mock_video.mp4';
  }

  @override
  void dispose() {}
}

PlatformRecorder getRecorder() => WebRecorder();
Future<List<dynamic>> getAvailableCameras() async => [];
