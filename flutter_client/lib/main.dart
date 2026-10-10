import 'package:flutter/material.dart';
import 'services/innvo_api.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const InnvoApp());
}

class InnvoApp extends StatelessWidget {
  const InnvoApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final apiService = InnvoApiService(baseUrl: "http://127.0.0.1:8000/api");

    return MaterialApp(
      title: 'Innvo AI Companion',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0E17),
        primaryColor: const Color(0xFF00E5FF),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00E5FF),
          secondary: Color(0xFF00FF9D),
          surface: Color(0xFF1E293B),
          background: Color(0xFF0A0E17),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0F172A),
          elevation: 0,
        ),
      ),
      home: HomeScreen(apiService: apiService),
    );
  }
}
