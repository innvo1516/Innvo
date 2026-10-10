import 'package:flutter/material.dart';
import '../services/innvo_api.dart';

class MemoriesScreen extends StatefulWidget {
  final InnvoApiService apiService;

  const MemoriesScreen({Key? key, required this.apiService}) : super(key: key);

  @override
  State<MemoriesScreen> createState() => _MemoriesScreenState();
}

class _MemoriesScreenState extends State<MemoriesScreen> {
  List<dynamic> _memories = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    final list = await widget.apiService.fetchMemories();
    setState(() {
      _memories = list;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        title: const Text("Permanent RL Memories", style: TextStyle(color: Color(0xFF00E5FF))),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00E5FF)))
          : _memories.isEmpty
              ? const Center(child: Text("No memories learned yet.", style: TextStyle(color: Colors.white54)))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _memories.length,
                  itemBuilder: (context, index) {
                    final m = _memories[index];
                    final double qScore = (m['q_value'] ?? 0.5).toDouble();
                    return Card(
                      color: const Color(0xFF1E293B),
                      margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Chip(
                                  backgroundColor: const Color(0xFF334155),
                                  label: Text(m['category'] ?? 'general', style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12)),
                                ),
                                Text(
                                  "Q-Score: ${qScore.toStringAsFixed(2)}",
                                  style: TextStyle(
                                    color: qScore >= 0.8 ? const Color(0xFF00FF9D) : Colors.amberAccent,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              m['content'] ?? '',
                              style: const TextStyle(color: Colors.white, fontSize: 15),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
