import 'recorder_stub.dart'
    if (dart.library.html) 'recorder_web.dart'
    if (dart.library.io) 'recorder_mobile.dart';

abstract class PlatformRecorder {
  Future<void> initialize();
  Future<void> startRecording();
  Future<String?> stopRecording();
  void dispose();

  static PlatformRecorder create() => getRecorder();
}

/// Returns available cameras (empty list on web).
Future<List<dynamic>> safeAvailableCameras() => getAvailableCameras();
