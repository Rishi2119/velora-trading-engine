import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'api_config.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() {
    if (statusCode != null) {
      return 'ApiException ($statusCode): $message';
    }
    return 'ApiException: $message';
  }
}

class ApiClient {
  String? _token;
  final http.Client _client = http.Client();
  static const Duration timeoutDuration = Duration(seconds: 15);

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('velora_token');
  }

  void updateToken(String? token) {
    _token = token;
  }

  Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  void _logRequest(String method, String url, {dynamic body}) {
    if (kDebugMode) {
      print('🌐 [API REQ] $method $url');
      if (body != null) print('📦 Body: $body');
    }
  }

  void _logResponse(http.Response response) {
    if (kDebugMode) {
      print('✅ [API RES] ${response.statusCode} ${response.request?.url}');
      if (response.statusCode >= 400 || response.body.length < 500) {
        print('📄 Data: ${response.body}');
      } else {
        print('📄 Data: <Large Payload ${response.body.length} bytes>');
      }
    }
  }

  void _logError(String method, String url, dynamic error) {
    if (kDebugMode) {
      print('❌ [API ERR] $method $url - $error');
    }
  }

  Future<dynamic> _processResponse(http.Response response) async {
    _logResponse(response);

    if (response.statusCode == 401) {
      updateToken(null);
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('velora_token');
      throw ApiException('Session expired. Please log in again.', 401);
    }
    
    dynamic data;
    try {
      data = jsonDecode(response.body);
    } catch (_) {
      data = {'message': response.body};
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return data;
    } else {
      final errorMessage = data['detail'] ?? data['error'] ?? data['message'] ?? 'HTTP Error ${response.statusCode}';
      throw ApiException(errorMessage, response.statusCode);
    }
  }

  Exception _handleNetworkError(dynamic error) {
    if (error.toString().contains('SocketException') || error.toString().contains('XMLHttpRequest')) {
      return ApiException('Network unreachable: Check if your server is running and accessible.', 503);
    } else if (error is TimeoutException) {
      return ApiException('Connection timeout: The server took too long to respond.', 408);
    }
    return ApiException('An unexpected error occurred: $error');
  }

  Future<dynamic> get(String endpoint) async {
    final url = '${ApiConfig.baseUrl}$endpoint';
    _logRequest('GET', url);
    
    try {
      final response = await _client
          .get(Uri.parse(url), headers: _headers)
          .timeout(timeoutDuration);
      return await _processResponse(response);
    } catch (e) {
      _logError('GET', url, e);
      if (e is ApiException) rethrow;
      throw _handleNetworkError(e);
    }
  }

  Future<dynamic> post(String endpoint, {Map<String, dynamic>? body}) async {
    final url = '${ApiConfig.baseUrl}$endpoint';
    _logRequest('POST', url, body: body);

    try {
      final response = await _client
          .post(
            Uri.parse(url),
            headers: _headers,
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(timeoutDuration);
      return await _processResponse(response);
    } catch (e) {
      _logError('POST', url, e);
      if (e is ApiException) rethrow;
      throw _handleNetworkError(e);
    }
  }

  Future<dynamic> delete(String endpoint) async {
    final url = '${ApiConfig.baseUrl}$endpoint';
    _logRequest('DELETE', url);

    try {
      final response = await _client
          .delete(Uri.parse(url), headers: _headers)
          .timeout(timeoutDuration);
      return await _processResponse(response);
    } catch (e) {
      _logError('DELETE', url, e);
      if (e is ApiException) rethrow;
      throw _handleNetworkError(e);
    }
  }
}
