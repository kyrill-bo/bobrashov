import 'package:flutter/material.dart';
import 'package:studycapsule/data/models/prompt.model.dart';
import 'package:studycapsule/data/models/chat_message.model.dart';
import 'package:studycapsule/data/repository/ai.repository.dart';
import 'package:studycapsule/ui/widgets/message_bubble.dart';
import 'package:studycapsule/ui/widgets/chat_input.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final AiRepository _aiRepo = AiRepository();
  final List<ChatMessage> _messages = [];
  final ScrollController _scrollController = ScrollController();
  bool _isLoading = false;

  // Limit conversation history to avoid API token limits
  static const int _maxHistoryLength = 20;

  @override
  void initState() {
    super.initState();
    // Add a welcome message
    _messages.add(
      ChatMessage(
        content: "Hello! I'm your AI assistant. How can I help you today?",
        sender: MessageSender.ai,
      ),
    );
  }

  void _handleSendMessage(String text) async {
    if (text.trim().isEmpty || _isLoading) return;

    // Add user message
    final userMessage = ChatMessage(content: text, sender: MessageSender.user);

    setState(() {
      _messages.add(userMessage);
      _isLoading = true;
    });

    // Add loading message for AI
    final loadingMessage = ChatMessage(
      content: '',
      sender: MessageSender.ai,
      isLoading: true,
    );

    setState(() {
      _messages.add(loadingMessage);
    });

    _scrollToBottom();

    try {
      // Prepare the conversation history for Gemini API
      // Convert all messages except the loading message to Contents format
      final conversationHistory = <Contents>[];

      // Get recent messages to stay within API limits
      final messagesToSend = _messages.where((msg) => !msg.isLoading).toList();
      final startIndex = messagesToSend.length > _maxHistoryLength
          ? messagesToSend.length - _maxHistoryLength
          : 0;

      for (int i = startIndex; i < messagesToSend.length; i++) {
        final message = messagesToSend[i];

        // Map MessageSender to role expected by Gemini API
        String role;
        if (message.sender == MessageSender.user) {
          role = 'user';
        } else {
          role = 'model'; // Gemini API uses 'model' for AI responses
        }

        conversationHistory.add(
          Contents(
            role: role,
            parts: [Parts(text: message.content)],
          ),
        );
      }

      final prompt = Prompt(contents: conversationHistory);
      final response = await _aiRepo.getAiResponse(prompt);

      // Remove loading message and add actual response
      setState(() {
        _messages.removeLast();
        _messages.add(ChatMessage(content: response, sender: MessageSender.ai));
        _isLoading = false;
      });

      _scrollToBottom();
    } catch (e) {
      // Remove loading message and add error message
      setState(() {
        _messages.removeLast();
        _messages.add(
          ChatMessage(
            content: "Sorry, I encountered an error: ${e.toString()}",
            sender: MessageSender.ai,
          ),
        );
        _isLoading = false;
      });

      _scrollToBottom();
    }
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

  void _clearChat() {
    setState(() {
      _messages.clear();
      _messages.add(
        ChatMessage(
          content: "Hello! I'm your AI assistant. How can I help you today?",
          sender: MessageSender.ai,
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Study Capsule'),
            if (_messages.isNotEmpty)
              Text(
                '${_messages.where((m) => !m.isLoading).length} Nachrichten',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurface.withAlpha(150),
                ),
              ),
          ],
        ),
        backgroundColor: theme.colorScheme.surfaceContainer,
        actions: [
          IconButton(
            icon: const Icon(Icons.clear_all),
            onPressed: _clearChat,
            tooltip: 'Clear chat',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.chat_bubble_outline,
                          size: 64,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Start a conversation!',
                          style: theme.textTheme.titleLarge?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      return MessageBubble(message: _messages[index]);
                    },
                  ),
          ),
          ChatInput(onSend: _handleSendMessage, isLoading: _isLoading),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }
}
