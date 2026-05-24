import 'package:dio/dio.dart';

import '../app_config.dart';
import '../models/report.dart';
import '../models/model_config.dart';

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  Dio get _dio => Dio(BaseOptions(
        baseUrl: AppConfig.baseUrl,
        connectTimeout: const Duration(seconds: 10),
        sendTimeout: const Duration(seconds: 120),
        receiveTimeout: const Duration(seconds: 120),
      ));

  Future<Map<String, dynamic>> uploadScore(String filePath,
      {String title = '未命名曲目'}) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
      'title': title,
    });
    final res = await _dio.post('/api/upload_score', data: form);
    return res.data as Map<String, dynamic>;
  }

  Future<EvaluateResult> evaluate(String videoPath,
      {String? scoreId, int? userId}) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(videoPath),
      if (scoreId != null) 'score_id': scoreId,
      if (userId != null) 'user_id': userId,
    });
    final res = await _dio.post('/api/evaluate', data: form);
    return EvaluateResult.fromJson(res.data as Map<String, dynamic>);
  }

  Future<ModelConfig> getConfig({bool reveal = false}) async {
    final res = await _dio.get('/api/config',
        queryParameters: {'reveal': reveal});
    return ModelConfig.fromJson(res.data as Map<String, dynamic>);
  }

  Future<void> updateConfig(Map<String, dynamic> patch) async {
    await _dio.post('/api/config', data: patch);
  }

  Future<Map<String, dynamic>> testLLM() async {
    final res = await _dio.post('/api/config/test');
    return res.data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> listReports({int? userId}) async {
    final res = await _dio.get('/api/reports',
        queryParameters: {if (userId != null) 'user_id': userId});
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<bool> ping() async {
    try {
      final res = await _dio.get('/health');
      return res.data['ok'] == true;
    } catch (_) {
      return false;
    }
  }
}
