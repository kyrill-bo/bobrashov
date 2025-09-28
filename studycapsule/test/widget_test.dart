// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

import 'package:studycapsule/main.dart';

void main() {
  setUp(() async {
    // Set up environment variables for testing
    dotenv.env.clear();
    dotenv.env['API_URL'] =
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent';
    dotenv.env['API_KEY'] = 'test_key';
  });

  testWidgets('Chat app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify that we have the main chat interface elements
    expect(find.text('Study Capsule'), findsOneWidget);
    expect(find.text('Type your message...'), findsOneWidget);
    expect(find.byIcon(Icons.send), findsOneWidget);

    // Verify welcome message is displayed
    expect(
      find.textContaining('Hello! I\'m your AI assistant'),
      findsOneWidget,
    );
  });

  testWidgets('Chat input test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Find the text field and enter some text
    final textField = find.byType(TextField);
    expect(textField, findsOneWidget);

    await tester.enterText(textField, 'Hello, AI!');
    await tester.pump();

    // Verify the text was entered
    expect(find.text('Hello, AI!'), findsOneWidget);
  });
}
