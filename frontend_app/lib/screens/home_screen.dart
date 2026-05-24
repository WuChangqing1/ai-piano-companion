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

class _HomeScreenState extends State<HomeScreen> {
  String? _scoreId;
  String _scoreName = '尚未上传';
  bool _uploading = false;

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
        _scoreId = res['score_id'] as String;
        _scoreName = result.files.single.name;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('曲谱解析成功:$_scoreName')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('上传失败:$e')),
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
      appBar: AppBar(
        title: const Text('AI 琴伴'),
        actions: [
          IconButton(
            icon: const Icon(Icons.bar_chart),
            tooltip: '历史报告',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ReportsScreen()),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: '设置',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFEDE7FF), Color(0xFFF6F1FF)],
                ),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('当前曲谱',
                      style: TextStyle(
                          fontSize: 14, color: Colors.black54)),
                  const SizedBox(height: 6),
                  Text(_scoreName,
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
            const SizedBox(height: 24),
            FilledButton.tonalIcon(
              onPressed: _uploading ? null : _pickAndUploadScore,
              icon: const Icon(Icons.upload_file),
              label: Text(_uploading ? '上传中…' : '上传曲谱'),
              style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18)),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _startPractice,
              icon: const Icon(Icons.play_arrow),
              label: const Text('开始练习'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 22),
                textStyle: const TextStyle(
                    fontSize: 20, fontWeight: FontWeight.w600),
              ),
            ),
            const Spacer(),
            const Center(
              child: Text('把手机后置摄像头对准琴键\n开始你的沉浸式练习吧 ♪',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.black54, height: 1.5)),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
