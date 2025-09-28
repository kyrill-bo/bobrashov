# Study Capsule - LLM Chat App

A simple and elegant Flutter chat application that integrates with Google's Gemini AI API to provide an interactive AI assistant experience.

## Features

- **Clean Chat Interface**: Modern Material Design 3 UI with message bubbles
- **Real-time AI Responses**: Integration with Google Gemini 2.5 Flash model
- **Conversation Context**: AI maintains conversation history for contextual responses
- **Responsive Design**: Adaptive layout that works on different screen sizes
- **Message History**: Persistent chat history during app session with visual counter
- **Loading States**: Visual feedback during AI response generation
- **Error Handling**: Graceful error handling with user-friendly messages
- **Clear Chat**: Option to clear chat history and start fresh
- **Smart History Management**: Automatically limits conversation history to prevent API token overflow

## Technical Architecture

### Core Components

- **Models**:
  - `ChatMessage` - Represents individual chat messages with sender, content, and timestamp
  - `Prompt` - Formats requests for the Gemini API
  
- **Services**:
  - `ApiService` - Handles HTTP requests using Dio with proper headers and error handling
  - `AiRepository` - Manages AI API calls and response parsing

- **UI Widgets**:
  - `MessageBubble` - Displays individual chat messages with proper styling
  - `ChatInput` - Handles user input with send button and loading states
  - `HomePage` - Main chat interface with message list and state management

### API Integration

The app uses Google's Gemini 2.5 Flash API through the following endpoint:

``` env
https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
```

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd studycapsule
   ```

2. **Install dependencies**

   ```bash
   flutter pub get
   ```

3. **Configure API Key**
   - Create a `.env` file in the root directory
   - Add your Google AI API key:

   ``` env
   API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent
   API_KEY=your_gemini_api_key_here
   ```

4. **Run the app**

   ```bash
   flutter run
   ```

## Dependencies

- `flutter`: Flutter SDK
- `dio ^5.9.0`: HTTP client for API requests
- `flutter_dotenv ^6.0.0`: Environment variable management
- `cupertino_icons ^1.0.8`: iOS-style icons

## Project Structure

``` md
lib/
├── main.dart                 # App entry point
├── data/
│   ├── models/
│   │   ├── chat_message.model.dart  # Chat message data model
│   │   └── prompt.model.dart        # API request models
│   └── repository/
│       └── ai.repository.dart       # AI service repository
├── services/
│   └── api.service.dart             # HTTP service layer
└── ui/
    ├── pages/
    │   └── home.page.dart           # Main chat page
    └── widgets/
        ├── chat_input.dart          # Message input widget
        └── message_bubble.dart      # Message display widget
```

## Features Implemented

✅ Google Gemini AI Integration  
✅ Modern Chat UI with Message Bubbles  
✅ Real-time Message Sending  
✅ Conversation History Context (AI remembers previous messages)  
✅ Loading States and Animations  
✅ Error Handling  
✅ Message History with Counter Display  
✅ Clear Chat Functionality  
✅ Responsive Design  
✅ Smart History Limiting (prevents API token overflow)  

## Usage

1. **Start Chatting**: Type your message in the input field at the bottom
2. **Send Message**: Tap the send button or press Enter
3. **View AI Response**: The AI will respond with helpful information
4. **Clear Chat**: Use the clear button in the app bar to start fresh
5. **Scroll History**: Scroll through previous messages in the chat

## Error Handling

The app includes comprehensive error handling for:

- Network connectivity issues
- API rate limiting
- Invalid API responses
- Empty message handling
- Loading state management

## Future Enhancements

Potential improvements could include:

- Message persistence across app restarts
- User authentication
- Multiple conversation threads
- File/image sharing capabilities
- Voice input/output
- Custom AI model selection
- Chat export functionality
