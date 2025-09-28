class Prompt {
  List<Contents> contents;

  Prompt({required this.contents});

  Map<String, dynamic> toJson() {
    return {'contents': contents.map((content) => content.toJson()).toList()};
  }
}

class SystemInstruction {
  String? language;
  String? tone;
  String? format;

  SystemInstruction({this.language, this.tone, this.format});

  Map<String, dynamic> toJson() {
    return {'language': language, 'tone': tone, 'format': format};
  }
}

class Contents {
  String role;
  List<Parts> parts;

  Contents({required this.role, required this.parts});

  Map<String, dynamic> toJson() {
    return {'role': role, 'parts': parts.map((part) => part.toJson()).toList()};
  }
}

class Parts {
  String text;

  Parts({required this.text});

  Map<String, dynamic> toJson() {
    return {'text': text};
  }
}
