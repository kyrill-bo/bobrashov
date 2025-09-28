import 'package:flutter/material.dart';
import 'package:sms_sender/sms_sender.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final controller = TextEditingController(text: "+4915563525349");

  Future<void> sendSms() async {
    List<Map<String, dynamic>> simCards = await SmsSender.getSimCards();

    await SmsSender.sendSms(
      phoneNumber: controller.text,
      message: "1866483",
      simSlot: simCards[0]['simSlot'],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home Page')),
      body: Column(
        children: [
          const Text('Welcome to the Home Page!'),
          const SizedBox(height: 16),
          const Text('This is a simple Flutter application.'),
          const SizedBox(height: 16),
          TextField(
            controller: controller,
            decoration: InputDecoration(
              labelText: 'Enter something',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: sendSms, child: const Text('Send SMS')),
        ],
      ),
    );
  }
}
