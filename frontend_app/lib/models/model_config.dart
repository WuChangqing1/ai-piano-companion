/// 模型配置 - 与后端 /api/config 字段对齐。
class ModelConfig {
  final LLMConfig llm;
  final TTSConfig tts;
  final PromptConfig prompt;

  ModelConfig({required this.llm, required this.tts, required this.prompt});

  factory ModelConfig.fromJson(Map<String, dynamic> j) => ModelConfig(
        llm: LLMConfig.fromJson(j['llm'] as Map<String, dynamic>),
        tts: TTSConfig.fromJson(j['tts'] as Map<String, dynamic>),
        prompt: PromptConfig.fromJson(j['prompt'] as Map<String, dynamic>),
      );
}

class LLMConfig {
  String provider;
  String baseUrl;
  String apiKey;
  String model;
  double temperature;
  int maxTokens;

  LLMConfig({
    required this.provider,
    required this.baseUrl,
    required this.apiKey,
    required this.model,
    required this.temperature,
    required this.maxTokens,
  });

  factory LLMConfig.fromJson(Map<String, dynamic> j) => LLMConfig(
        provider: j['provider'] as String,
        baseUrl: j['base_url'] as String,
        apiKey: j['api_key'] as String,
        model: j['model'] as String,
        temperature: (j['temperature'] as num).toDouble(),
        maxTokens: j['max_tokens'] as int,
      );

  Map<String, dynamic> toJson() => {
        'provider': provider,
        'base_url': baseUrl,
        'api_key': apiKey,
        'model': model,
        'temperature': temperature,
        'max_tokens': maxTokens,
      };
}

class TTSConfig {
  String engine;
  String voice;
  String rate;
  String pitch;

  TTSConfig({
    required this.engine,
    required this.voice,
    required this.rate,
    required this.pitch,
  });

  factory TTSConfig.fromJson(Map<String, dynamic> j) => TTSConfig(
        engine: j['engine'] as String,
        voice: j['voice'] as String,
        rate: j['rate'] as String,
        pitch: j['pitch'] as String,
      );

  Map<String, dynamic> toJson() => {
        'engine': engine,
        'voice': voice,
        'rate': rate,
        'pitch': pitch,
      };
}

class PromptConfig {
  String system;
  String userTemplate;

  PromptConfig({required this.system, required this.userTemplate});

  factory PromptConfig.fromJson(Map<String, dynamic> j) => PromptConfig(
        system: j['system'] as String,
        userTemplate: j['user_template'] as String,
      );

  Map<String, dynamic> toJson() => {
        'system': system,
        'user_template': userTemplate,
      };
}
