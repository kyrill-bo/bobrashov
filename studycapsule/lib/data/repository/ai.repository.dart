import 'package:studycapsule/data/models/prompt.model.dart';
import 'package:studycapsule/services/api.service.dart';

class AiRepository {
  static final _api = ApiService.instance;

  Future<String> getAiResponse(Prompt prompt) async {
    final response = await _api.postData('', data: prompt.toJson());

    if (response != null && response['candidates'] != null) {
      final candidates = response['candidates'] as List;
      if (candidates.isNotEmpty) {
        final content = candidates[0]['content'];
        if (content != null && content['parts'] != null) {
          final parts = content['parts'] as List;
          if (parts.isNotEmpty && parts[0]['text'] != null) {
            return parts[0]['text'] as String;
          }
        }
      }
    }

    throw Exception('Invalid response from AI service');
  }
}
