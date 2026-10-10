import 'package:flutter/material.dart';
import '../models/message.dart';
import '../services/innvo_api.dart';
import '../widgets/glowing_orb.dart';
import 'memories_screen.dart';
import 'tools_screen.dart';
import 'rules_screen.dart';

class HomeScreen extends StatefulWidget {
  final InnvoApiService apiService;

  const HomeScreen({Key? key, required this.apiService}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];

  bool _isThinking = false;
  bool _isOnline = false;
  String? _pendingProposal;

  @override
  void initState() {
    super.initState();
    _checkServerStatus();
    _addInitialGreeting();
  }

  void _addInitialGreeting() {
    _messages.add(
      ChatMessage(
        text: "Namaste Sir! Main Innvo hoon. Main aapki kya madad kar sakta hoon?",
        isUser: false,
        timestamp: DateTime.now(),
      ),
    );
  }

  Future<void> _checkServerStatus() async {
    final health = await widget.apiService.checkHealth();
    setState(() {
      _isOnline = health['status'] == 'online';
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _handleSend([String? presetText]) async {
    final text = (presetText ?? _textController.text).trim();
    if (text.isEmpty) return;

    if (presetText == null) {
      _textController.clear();
    }

    setState(() {
      _messages.add(
        ChatMessage(
          text: text,
          isUser: true,
          timestamp: DateTime.now(),
        ),
      );
      _isThinking = true;
      _pendingProposal = null;
    });
    _scrollToBottom();

    final response = await widget.apiService.sendMessage(text);

    setState(() {
      _isThinking = false;
      if (response != null) {
        _messages.add(response);
        if (response.pendingApproval && response.proposal != null) {
          _pendingProposal = response.proposal;
        }
      }
    });
    _scrollToBottom();
  }

  void _handleApproval(bool approved) {
    final responseText = approved ? "Haan, save kar lo" : "Nahi, rehne do";
    setState(() {
      _pendingProposal = null;
    });
    _handleSend(responseText);
  }

  void _showSettingsDialog() {
    final ipController = TextEditingController(text: widget.apiService.baseUrl);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF161B22),
        title: const Text("Innvo Core Engine Settings", style: TextStyle(color: Color(0xFF00E5FF))),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              "Local API Bridge URL (e.g. http://192.168.1.15:8000/api for Phone on Wi-Fi):",
              style: TextStyle(color: Colors.white70, fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: ipController,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                filled: true,
                fillColor: Color(0xFF0D1117),
                border: OutlineInputBorder(),
                hintText: "http://127.0.0.1:8000/api",
                hintStyle: TextStyle(color: Colors.white30),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel", style: TextStyle(color: Colors.white60)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00E5FF)),
            onPressed: () {
              widget.apiService.setBaseUrl(ipController.text.trim());
              Navigator.pop(context);
              _checkServerStatus();
            },
            child: const Text("Save & Reconnect", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E17),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0F172A),
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _isOnline ? const Color(0xFF00FF9D) : Colors.redAccent,
                boxShadow: [
                  BoxShadow(
                    color: (_isOnline ? const Color(0xFF00FF9D) : Colors.redAccent).withOpacity(0.6),
                    blurRadius: 8,
                    spreadRadius: 2,
                  )
                ],
              ),
            ),
            const SizedBox(width: 10),
            const Text(
              "INNVO CORE",
              style: TextStyle(
                color: Color(0xFF00E5FF),
                fontWeight: FontWeight.bold,
                letterSpacing: 2.0,
                fontSize: 16,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined, color: Colors.white70),
            onPressed: _showSettingsDialog,
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white70),
            onPressed: () {
              widget.apiService.clearHistory();
              setState(() {
                _messages.clear();
                _addInitialGreeting();
              });
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Holographic Glowing Orb Banner
          Container(
            padding: const EdgeInsets.symmetric(vertical: 18),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0xFF0F172A), Color(0xFF0A0E17)],
              ),
            ),
            child: GlowingOrb(
              isThinking: _isThinking,
              size: 110,
            ),
          ),

          // Shortcut Pills
          Container(
            height: 38,
            margin: const EdgeInsets.symmetric(vertical: 4),
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              children: [
                _buildShortcutPill("🧠 Memories", () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => MemoriesScreen(apiService: widget.apiService)));
                }),
                _buildShortcutPill("🛠️ Dynamic Skills", () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => ToolsScreen(apiService: widget.apiService)));
                }),
                _buildShortcutPill("⚖️ Constitution", () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => RulesScreen(apiService: widget.apiService)));
                }),
                _buildShortcutPill("⚡ Battery Status", () => _handleSend("Battery kitni hai?")),
                _buildShortcutPill("🕒 Live Time", () => _handleSend("What time is it?")),
              ],
            ),
          ),

          // Chat Messages View
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _buildMessageBubble(msg);
              },
            ),
          ),

          // Interactive Approval Sheet (Haan / Nahi)
          if (_pendingProposal != null)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF1E1B4B),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF818CF8), width: 1.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.psychology_alt_rounded, color: Color(0xFF818CF8), size: 18),
                      SizedBox(width: 6),
                      Text("Innvo Learning Proposal:", style: TextStyle(color: Color(0xFFA5B4FC), fontWeight: FontWeight.bold, fontSize: 13)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(_pendingProposal!, style: const TextStyle(color: Colors.white, fontSize: 14)),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      OutlinedButton(
                        style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.redAccent)),
                        onPressed: () => _handleApproval(false),
                        child: const Text("Nahi (Discard)", style: TextStyle(color: Colors.redAccent)),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00FF9D)),
                        onPressed: () => _handleApproval(true),
                        child: const Text("Haan (Save to Memory)", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  )
                ],
              ),
            ),

          // Bottom Input Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            color: const Color(0xFF0F172A),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textController,
                    onSubmitted: (_) => _handleSend(),
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: "Speak or type in Hindi/English...",
                      hintStyle: const TextStyle(color: Colors.white38),
                      filled: true,
                      fillColor: const Color(0xFF1E293B),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(25),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  icon: const Icon(Icons.send_rounded, color: Color(0xFF00E5FF)),
                  onPressed: () => _handleSend(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildShortcutPill(String title, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFF00E5FF).withOpacity(0.3)),
        ),
        child: Center(
          child: Text(title, style: const TextStyle(color: Colors.white, fontSize: 12)),
        ),
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    final isUser = msg.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.all(14),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF0284C7) : const Color(0xFF1E293B),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
          border: Border.all(
            color: isUser ? const Color(0xFF38BDF8) : const Color(0xFF334155),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!isUser && msg.toolUsed != null)
              Container(
                margin: const EdgeInsets.only(bottom: 6),
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFF00FF9D).withOpacity(0.2),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  "Tool: ${msg.toolUsed}",
                  style: const TextStyle(color: Color(0xFF00FF9D), fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
            Text(
              msg.text,
              style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.3),
            ),
          ],
        ),
      ),
    );
  }
}
