import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiService {
  static String baseUrl = dotenv.get('API_URL');

  // This class will handle API requests and responses
  // You can use packages like http or dio for making HTTP requests
  static final ApiService instance = ApiService._singleton();
  ApiService._singleton() {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': dotenv.get('API_KEY'),
          // 'Authorization': 'Bearer token', // optional
        },
      ),
    );
  }

  late final Dio _dio;

  Future<dynamic> fetchData(
    String endpoint, {
    Map<String, dynamic>? data,
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response = await _dio.get(
        endpoint,
        data: data,
        queryParameters: queryParameters,
      );
      return response.data;
    } catch (e) {
      _handleError(e);
    }
  }

  Future<dynamic> postData(
    String endpoint, {
    Map<String, dynamic>? data,
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      final response = await _dio.post(
        endpoint,
        data: data,
        queryParameters: queryParameters,
      );
      return response.data;
    } catch (e) {
      _handleError(e);
    }
  }

  Future<dynamic> putData(String endpoint, Map<String, dynamic> data) async {
    try {
      final response = await _dio.put(endpoint, data: data);
      return response.data;
    } catch (e) {
      _handleError(e);
    }
  }

  Future<void> deleteData(String endpoint) async {
    try {
      await _dio.delete(endpoint);
    } catch (e) {
      _handleError(e);
    }
  }

  void _handleError(Object error) {
    if (error is DioException) {
      final statusCode = error.response?.statusCode;
      final message = error.response?.data ?? error.message;

      throw Exception('Dio-Fehler [${statusCode ?? 'unbekannt'}]: $message');
    } else {
      throw Exception('Unbekannter Fehler: $error');
    }
  }

  void updateLocale(String locale) {
    _dio.options.headers['Accept-Language'] = locale;
  }
}
