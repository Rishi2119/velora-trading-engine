import 'package:shared_preferences/shared_preferences.dart';
import 'api_client.dart';

class AuthService {
  final ApiClient _client;

  AuthService(this._client);

  bool get isLoggedIn => _token != null;
  String? _token;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('velora_token');
    _client.updateToken(_token);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final data = await _client.post(
      '/auth/login',
      body: {'email': email, 'password': password},
    );
    
    _token = data['access_token'];
    _client.updateToken(_token);
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('velora_token', _token!);
    return data;
  }

  Future<void> logout() async {
    _token = null;
    _client.updateToken(null);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('velora_token');
  }
}
