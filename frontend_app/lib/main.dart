import 'package:flutter/material.dart';

import 'app_config.dart';
import 'webview_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AppConfig.init();
  runApp(const AiQinbanApp());
}

class AiQinbanApp extends StatelessWidget {
  const AiQinbanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI琴伴',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF8E7CFF),
          brightness: Brightness.light,
        ),
        fontFamily: 'PingFang SC',
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
      ),
      home: const WebViewShell(),
    );
  }
}
