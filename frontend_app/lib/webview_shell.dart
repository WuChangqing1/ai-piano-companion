import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'app_config.dart';
import 'services/recorder.dart' as rec;

class WebViewShell extends StatefulWidget {
  const WebViewShell({super.key});

  @override
  State<WebViewShell> createState() => _WebViewShellState();
}

class _WebViewShellState extends State<WebViewShell> {
  late final WebViewController _controller;
  final Dio _dio = Dio();
  rec.PlatformRecorder? _recorder;
  bool _recording = false;

  @override
  void initState() {
    super.initState();
    _initWebView();
  }

  Future<void> _initWebView() async {
    final html = await rootBundle.loadString('assets/demo/Demo.html');

    // Extract HTML + icons to temp dir so WebView can resolve relative <img> paths
    final tmpDir = await getTemporaryDirectory();
    final demoDir = Directory('${tmpDir.path}/demo');
    final iconsDir = Directory('${demoDir.path}/icons');
    if (!await iconsDir.exists()) {
      await iconsDir.create(recursive: true);
    }

    final iconNames = [
      'clock.png', 'ePerson.png', 'flow.png', 'hand.png',
      'logo.png', 'note.png', 'play.png', 'quote.png',
      'report.png', 'reset.png', 'rhythm.png', 'settings.png',
      'speaker.png', 'tip.png', 'upload.png',
    ];
    for (final name in iconNames) {
      try {
        final data = await rootBundle.load('assets/icons/$name');
        await File('${iconsDir.path}/$name').writeAsBytes(data.buffer.asUint8List());
      } catch (_) {}
    }

    final htmlPath = '${demoDir.path}/index.html';
    await File(htmlPath).writeAsString(html);

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..addJavaScriptChannel(
        'Flutter',
        onMessageReceived: _onJsMessage,
      )
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (_) {
            _controller.runJavaScript(
              "localStorage.setItem('baseUrl', '${AppConfig.baseUrl}');"
              "BACKEND_BASE = '${AppConfig.baseUrl}';",
            );
          },
        ),
      )
      ..loadFile(htmlPath);

    setState(() {});
  }

  Future<void> _onJsMessage(JavaScriptMessage msg) async {
    try {
      final data = jsonDecode(msg.message) as Map<String, dynamic>;
      final action = data['action'] as String?;

      switch (action) {
        case 'startRecording':
          await _startRecording();
          break;
        case 'stopRecording':
          await _stopRecording();
          break;
        default:
          break;
      }
    } catch (e) {
      debugPrint('WebView message error: $e');
    }
  }

  Future<void> _startRecording() async {
    try {
      _recorder = rec.PlatformRecorder.create();
      await _recorder!.initialize();
      await _recorder!.startRecording();
    } catch (e) {
      debugPrint('Start recording error: $e');
      _controller.runJavaScript(
        "go('home'); toast('录制启动失败: ${e.toString().replaceAll("'", "\\'")}')",
      );
    }
  }

  Future<void> _stopRecording() async {
    if (_recorder == null) return;
    try {
      final path = await _recorder!.stopRecording();
      _recorder!.dispose();
      _recorder = null;

      if (path == null) {
        _controller.runJavaScript("go('home'); toast('录制文件为空')");
        return;
      }

      // Tell JS we're evaluating
      _controller.runJavaScript(
        "window.postMessage({type:'evaluateStart'}, '*')",
      );

      // Upload to backend
      final file = File(path);
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(path, filename: 'recording.mp4'),
      });

      final baseUrl = AppConfig.baseUrl;
      final resp = await _dio.post(
        '$baseUrl/api/evaluate',
        data: formData,
        options: Options(
          sendTimeout: const Duration(minutes: 10),
          receiveTimeout: const Duration(minutes: 10),
        ),
      );

      if (resp.statusCode == 200) {
        final reportData = resp.data;
        final reportJson = jsonEncode(reportData);
        // Inject report into WebView
        _controller.runJavaScript(
          "window.postMessage({type:'report', data:$reportJson}, '*')",
        );
      } else {
        _controller.runJavaScript("go('home'); toast('分析失败')");
      }

      // Clean up temp file
      try { await file.delete(); } catch (_) {}
    } catch (e) {
      debugPrint('Stop recording error: $e');
      _controller.runJavaScript("go('home'); toast('上传失败: 请检查后端连接')");
      try { _recorder?.dispose(); } catch (_) {}
      _recorder = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: WebViewWidget(controller: _controller),
      ),
    );
  }

  @override
  void dispose() {
    _recorder?.dispose();
    super.dispose();
  }
}
