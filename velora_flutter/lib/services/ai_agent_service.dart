import 'api_client.dart';

class AiAgentService {
  final ApiClient _client;

  AiAgentService(this._client);

  Future<Map<String, dynamic>> getAgentStatus() async {
    return await _client.get('/ai/status');
  }

  Future<Map<String, dynamic>> getAgentThoughts() async {
    return await _client.get('/ai/thoughts');
  }

  Future<void> startAgent() async {
    await _client.post('/ai/start');
  }

  Future<void> stopAgent() async {
    await _client.post('/ai/stop');
  }
}
