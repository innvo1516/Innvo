import 'package:flutter/material.dart';
import '../services/innvo_api.dart';

class ToolsScreen extends StatefulWidget {
  final InnvoApiService apiService;

  const ToolsScreen({Key? key, required this.apiService}) : super(key: key);

  @override
  State<ToolsScreen> createState() => _ToolsScreenState();
}

class _ToolsScreenState extends State<ToolsScreen> {
  List<dynamic> _tools = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    final list = await widget.apiService.fetchTools();
    setState(() {
      _tools = list;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text("Dynamic & Built-in Skills", style: TextStyle(color: Color(0xFF00E5FF))),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _tools.length,
              itemBuilder: (context, index) {
                final t = _tools[index];
                final bool isDynamic = t['type'] == 'dynamic';
                return Card(
                  color: const Color(0xFF1E293B),
                  margin: const EdgeInsets.only(bottom: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isDynamic ? const Color(0xFF818CF8).withOpacity(0.2) : const Color(0xFF00FF9D).withOpacity(0.2),
                      child: Icon(
                        isDynamic ? Icons.auto_awesome_rounded : Icons.build_rounded,
                        color: isDynamic ? const Color(0xFF818CF8) : const Color(0xFF00FF9D),
                      ),
                    ),
                    title: Text(t['name'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    subtitle: Text(t['description'] ?? '', style: const TextStyle(color: Colors.white70, fontSize: 13)),
                    trailing: Text(
                      isDynamic ? "Self-Learned" : "Builtin",
                      style: TextStyle(color: isDynamic ? const Color(0xFF818CF8) : const Color(0xFF00FF9D), fontSize: 12),
                    ),
                  ),
                );
              },
            ),
    );
  }
}
