import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/message.dart';

class InnvoApiService {
  String baseUrl;

  InnvoApiService({this.baseUrl = "http://127.0.0.1:8000/api"});

  void setBaseUrl(String newUrl) {
    baseUrl = newUrl.endsWith('/') ? newUrl.substring(0, newUrl.length - 1) : newUrl;
  }

  Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health')).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
    } catch (_) {}
    return {"status": "offline"};
  }

  Future<ChatMessage?> sendMessage(String text) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'text': text}),
      ).timeout(const Duration(seconds: 45));

      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return ChatMessage.fromApiResponse(data);
      }
    } catch (e) {
      return ChatMessage(
        text: "[Connection Error]: Could not reach Innvo Engine at $baseUrl. Make sure 'python main.py --server' is running.",
        isUser: false,
        timestamp: DateTime.now(),
      );
    }
    return null;
  }

  Future<List<dynamic>> fetchMemories() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/memories')).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return data['memories'] ?? [];
      }
    } catch (_) {}
    return [];
  }

  Future<List<dynamic>> fetchTools() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/tools')).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return data['tools'] ?? [];
      }
    } catch (_) {}
    return [];
  }

  Future<List<dynamic>> fetchRules() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/rules')).timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        return data['laws'] ?? [];
      }
    } catch (_) {}
    return [];
  }

  Future<bool> clearHistory() async {
    try {
      final response = await http.post(Uri.parse('$baseUrl/clear')).timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> toggleIdleLearning(bool enable) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/idle'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'enable': enable}),
      ).timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
