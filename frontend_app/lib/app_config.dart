import 'package:shared_preferences/shared_preferences.dart';

/// 全局应用配置 - 持久化 baseUrl,允许用户在设置页修改。
class AppConfig {
  static const String _kBaseUrl = 'base_url';
  static const String defaultBaseUrl = 'http://localhost:8000';

  static late SharedPreferences _prefs;

  static Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  static String get baseUrl => _prefs.getString(_kBaseUrl) ?? defaultBaseUrl;

  static Future<void> setBaseUrl(String url) async {
    await _prefs.setString(_kBaseUrl, url.trim());
  }
}
