import 'package:flutter/material.dart';

import '../app_config.dart';
import '../models/model_config.dart';
import '../services/api_client.dart';

/// 设置页 - 用户自定义模型 API 的核心入口
/// 1. 修改后端地址(baseUrl,本地持久化)
/// 2. 修改 LLM/TTS/Prompt 配置(同步到后端 /api/config)
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _baseUrlCtrl;
  late TextEditingController _llmBaseUrlCtrl;
  late TextEditingController _llmApiKeyCtrl;
  late TextEditingController _llmModelCtrl;
  late TextEditingController _llmTemperatureCtrl;
  late TextEditingController _llmMaxTokensCtrl;
  late TextEditingController _ttsVoiceCtrl;
  late TextEditingController _ttsEngineCtrl;
  late TextEditingController _promptSystemCtrl;
  late TextEditingController _promptUserTplCtrl;

  ModelConfig? _config;
  bool _loading = true;
  bool _saving = false;
  String? _testMsg;

  static const _presets = <String, Map<String, String>>{
    'DeepSeek': {
      'base_url': 'https://api.deepseek.com/v1',
      'model': 'deepseek-chat',
    },
    '通义千问 (DashScope OpenAI 兼容)': {
      'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      'model': 'qwen-plus',
    },
    '智谱 GLM': {
      'base_url': 'https://open.bigmodel.cn/api/paas/v4',
      'model': 'glm-4',
    },
    'Moonshot Kimi': {
      'base_url': 'https://api.moonshot.cn/v1',
      'model': 'moonshot-v1-8k',
    },
    '本地 Ollama': {
      'base_url': 'http://127.0.0.1:11434/v1',
      'model': 'qwen2.5:7b',
    },
  };

  @override
  void initState() {
    super.initState();
    _baseUrlCtrl = TextEditingController(text: AppConfig.baseUrl);
    _llmBaseUrlCtrl = TextEditingController();
    _llmApiKeyCtrl = TextEditingController();
    _llmModelCtrl = TextEditingController();
    _llmTemperatureCtrl = TextEditingController();
    _llmMaxTokensCtrl = TextEditingController();
    _ttsVoiceCtrl = TextEditingController();
    _ttsEngineCtrl = TextEditingController();
    _promptSystemCtrl = TextEditingController();
    _promptUserTplCtrl = TextEditingController();
    _loadConfig();
  }

  Future<void> _loadConfig() async {
    setState(() => _loading = true);
    try {
      final cfg = await ApiClient.instance.getConfig();
      _llmBaseUrlCtrl.text = cfg.llm.baseUrl;
      _llmApiKeyCtrl.text = ''; // 后端返回掩码,用户重新输入才会更新
      _llmModelCtrl.text = cfg.llm.model;
      _llmTemperatureCtrl.text = cfg.llm.temperature.toString();
      _llmMaxTokensCtrl.text = cfg.llm.maxTokens.toString();
      _ttsVoiceCtrl.text = cfg.tts.voice;
      _ttsEngineCtrl.text = cfg.tts.engine;
      _promptSystemCtrl.text = cfg.prompt.system;
      _promptUserTplCtrl.text = cfg.prompt.userTemplate;
      setState(() {
        _config = cfg;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('读取配置失败:$e\n请先在上方设置正确的后端地址')),
      );
    }
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await AppConfig.setBaseUrl(_baseUrlCtrl.text);
      final patch = <String, dynamic>{
        'llm': {
          'base_url': _llmBaseUrlCtrl.text.trim(),
          'model': _llmModelCtrl.text.trim(),
          'temperature':
              double.tryParse(_llmTemperatureCtrl.text.trim()) ?? 0.8,
          'max_tokens':
              int.tryParse(_llmMaxTokensCtrl.text.trim()) ?? 200,
        },
        'tts': {
          'engine': _ttsEngineCtrl.text.trim(),
          'voice': _ttsVoiceCtrl.text.trim(),
        },
        'prompt': {
          'system': _promptSystemCtrl.text,
          'user_template': _promptUserTplCtrl.text,
        },
      };
      // api_key 留空表示不修改
      final newKey = _llmApiKeyCtrl.text.trim();
      if (newKey.isNotEmpty) {
        (patch['llm'] as Map<String, dynamic>)['api_key'] = newKey;
      }
      await ApiClient.instance.updateConfig(patch);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('已保存,新配置立即生效')),
      );
      _llmApiKeyCtrl.clear();
      _loadConfig();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('保存失败:$e')),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _test() async {
    setState(() => _testMsg = '测试中…');
    final res = await ApiClient.instance.testLLM();
    setState(() {
      _testMsg = res['ok'] == true
          ? '连通成功 ✓\n返回:${res['sample']}'
          : '失败:${res['error']}';
    });
  }

  void _applyPreset(String name) {
    final p = _presets[name];
    if (p == null) return;
    setState(() {
      _llmBaseUrlCtrl.text = p['base_url']!;
      _llmModelCtrl.text = p['model']!;
    });
  }

  @override
  void dispose() {
    for (final c in [
      _baseUrlCtrl,
      _llmBaseUrlCtrl,
      _llmApiKeyCtrl,
      _llmModelCtrl,
      _llmTemperatureCtrl,
      _llmMaxTokensCtrl,
      _ttsVoiceCtrl,
      _ttsEngineCtrl,
      _promptSystemCtrl,
      _promptUserTplCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('设置'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadConfig,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _section('后端服务'),
                TextField(
                  controller: _baseUrlCtrl,
                  decoration: const InputDecoration(
                    labelText: '后端 Base URL',
                    hintText: 'http://192.168.1.100:8000',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 24),
                _section('LLM 服务(自定义模型 API)'),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: _presets.keys
                      .map((k) => ActionChip(
                            label: Text(k),
                            onPressed: () => _applyPreset(k),
                          ))
                      .toList(),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _llmBaseUrlCtrl,
                  decoration: const InputDecoration(
                    labelText: 'LLM Base URL(OpenAI 兼容)',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _llmApiKeyCtrl,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'API Key',
                    hintText: _config?.llm.apiKey.isNotEmpty == true
                        ? '已保存(${_config!.llm.apiKey}),留空表示不修改'
                        : '请输入',
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _llmModelCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Model 名称',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _llmTemperatureCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Temperature',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: _llmMaxTokensCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(
                          labelText: 'Max Tokens',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: _test,
                  icon: const Icon(Icons.wifi_tethering),
                  label: const Text('测试 LLM 连通性'),
                ),
                if (_testMsg != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(_testMsg!,
                        style: const TextStyle(color: Colors.black54)),
                  ),
                const SizedBox(height: 24),
                _section('TTS 语音'),
                TextField(
                  controller: _ttsEngineCtrl,
                  decoration: const InputDecoration(
                    labelText: '引擎',
                    hintText: 'edge-tts / cosyvoice',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _ttsVoiceCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Voice',
                    hintText: 'zh-CN-XiaoxiaoNeural',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 24),
                _section('Prompt 模板'),
                TextField(
                  controller: _promptSystemCtrl,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'System Prompt',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _promptUserTplCtrl,
                  maxLines: 5,
                  decoration: const InputDecoration(
                    labelText: 'User Prompt 模板',
                    hintText: '可用占位:{wrong_notes}/{missing_notes}/{hand_issues}',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 32),
                FilledButton(
                  onPressed: _saving ? null : _save,
                  style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 18)),
                  child: Text(_saving ? '保存中…' : '保存全部'),
                ),
                const SizedBox(height: 32),
              ],
            ),
    );
  }

  Widget _section(String title) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(title,
            style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Color(0xFF6750A4))),
      );
}
