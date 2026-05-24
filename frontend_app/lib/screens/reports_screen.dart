import 'package:flutter/material.dart';

import '../services/api_client.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final list = await ApiClient.instance.listReports();
      setState(() {
        _items = list;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('加载失败:$e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('历史报告')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? const Center(child: Text('还没有练习记录哦'))
              : ListView.separated(
                  itemCount: _items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final r = _items[i];
                    return ListTile(
                      leading: CircleAvatar(
                        backgroundColor: const Color(0xFFEDE7FF),
                        child: Text('${r['overall_score']}',
                            style: const TextStyle(
                                color: Color(0xFF6750A4),
                                fontWeight: FontWeight.bold)),
                      ),
                      title: Text(r['teacher_comment'] ?? '',
                          maxLines: 2, overflow: TextOverflow.ellipsis),
                      subtitle: Text(r['created_at'] ?? ''),
                    );
                  },
                ),
    );
  }
}
