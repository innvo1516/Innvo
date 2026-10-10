class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final String? toolUsed;
  final bool searchUsed;
  final bool pendingApproval;
  final String? proposal;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.toolUsed,
    this.searchUsed = false,
    this.pendingApproval = false,
    this.proposal,
  });

  factory ChatMessage.fromApiResponse(Map<String, dynamic> json) {
    return ChatMessage(
      text: json['reply'] ?? '',
      isUser: false,
      timestamp: DateTime.now(),
      toolUsed: json['tool_used'],
      searchUsed: json['search_used'] ?? false,
      pendingApproval: json['pending_approval'] ?? false,
      proposal: json['proposal'],
    );
  }
}
