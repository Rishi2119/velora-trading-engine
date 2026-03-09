import 'api_client.dart';

class TradingService {
  final ApiClient _client;

  TradingService(this._client);

  Future<Map<String, dynamic>> getStats() async {
    return await _client.get('/trading/stats');
  }

  Future<Map<String, dynamic>> getOpenPositions() async {
    return await _client.get('/trading/open-positions');
  }

  Future<Map<String, dynamic>> getTradeHistory({int days = 7}) async {
    return await _client.get('/trading/history?days=$days');
  }

  Future<void> toggleKillSwitch(bool activate) async {
    if (activate) {
      await _client.post('/trading/kill-switch/activate');
    } else {
      await _client.delete('/trading/kill-switch');
    }
  }
}
