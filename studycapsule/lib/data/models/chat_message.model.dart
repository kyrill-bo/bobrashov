enum MessageSender { user, ai }

class ChatMessage {
  final String content;
  final MessageSender sender;
  final DateTime timestamp;
  final bool isLoading;

  ChatMessage({
    required this.content,
    required this.sender,
    DateTime? timestamp,
    this.isLoading = false,
  }) : timestamp = timestamp ?? DateTime.now();

  ChatMessage copyWith({
    String? content,
    MessageSender? sender,
    DateTime? timestamp,
    bool? isLoading,
  }) {
    return ChatMessage(
      content: content ?? this.content,
      sender: sender ?? this.sender,
      timestamp: timestamp ?? this.timestamp,
      isLoading: isLoading ?? this.isLoading,
    );
  }
}
