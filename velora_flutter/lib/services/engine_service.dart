import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'api_client.dart';
import 'api_config.dart';

/// Engine state snapshot from backend
class EngineState {
  final bool killSwitchActive;
  final String killSwitchReason;
  final bool mt5Connected;
  final double balance;
  final double equity;
  final double freeMargin;
  final double dailyPnl;
  final int dailyTrades;
  final int currentPositions;
  final String session;
  final bool wsConnected;
  final String regime;
  final String agentThought;

  const EngineState({
    this.killSwitchActive = false,
    this.killSwitchReason = '',
    this.mt5Connected = false,
    this.balance = 0,
    this.equity = 0,
    this.freeMargin = 0,
    this.dailyPnl = 0,
    this.dailyTrades = 0,
    this.currentPositions = 0,
    this.session = 'unknown',
    this.wsConnected = false,
    this.regime = 'TRENDING',
    this.agentThought = 'Awaiting analysis...',
  });

  EngineState copyWith({
    bool? killSwitchActive, String? killSwitchReason, bool? mt5Connected,
    double? balance, double? equity, double? freeMargin, double? dailyPnl,
    int? dailyTrades, int? currentPositions, String? session, bool? wsConnected,
    String? regime, String? agentThought,
  }) => EngineState(
    killSwitchActive: killSwitchActive ?? this.killSwitchActive,
    killSwitchReason: killSwitchReason ?? this.killSwitchReason,
    mt5Connected: mt5Connected ?? this.mt5Connected,
    balance: balance ?? this.balance,
    equity: equity ?? this.equity,
    freeMargin: freeMargin ?? this.freeMargin,
    dailyPnl: dailyPnl ?? this.dailyPnl,
    dailyTrades: dailyTrades ?? this.dailyTrades,
    currentPositions: currentPositions ?? this.currentPositions,
    session: session ?? this.session,
    wsConnected: wsConnected ?? this.wsConnected,
    regime: regime ?? this.regime,
    agentThought: agentThought ?? this.agentThought,
  );
}

class EngineService extends ChangeNotifier {
  final ApiClient _api;
  EngineState _state = const EngineState();
  WebSocketChannel? _ws;
  Timer? _reconnectTimer;
  Timer? _pollTimer;
  bool _disposed = false;

  EngineService(this._api);

  EngineState get state => _state;

  void _update(EngineState updated) {
    _state = updated;
    notifyListeners();
  }

  // ── Poll + WebSocket hybrid ──────────────────────────────────────────────

  Future<void> init() async {
    await _fetchStatus();
    _connectWS();
    // Poll every 10s as fallback to WS
    _pollTimer = Timer.periodic(const Duration(seconds: 10), (_) => _fetchStatus());
  }

  void _connectWS() {
    if (_disposed) return;
    try {
      final wsUrl = ApiConfig.wsUrl;
      _ws = WebSocketChannel.connect(Uri.parse(wsUrl));
      _update(_state.copyWith(wsConnected: true));

      _ws!.stream.listen(
        (raw) => _handleWsMessage(raw),
        onError: (_) => _scheduleReconnect(),
        onDone: () => _scheduleReconnect(),
        cancelOnError: true,
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    _update(_state.copyWith(wsConnected: false));
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), _connectWS);
  }

  void _handleWsMessage(dynamic raw) {
    try {
      final event = jsonDecode(raw as String) as Map<String, dynamic>;
      final type = event['type'];
      final data = (event['data'] as Map<String, dynamic>?) ?? {};

      switch (type) {
        case 'heartbeat':
          final mt5 = data['mt5'] as Map<String, dynamic>? ?? {};
          _update(_state.copyWith(
            mt5Connected: mt5['connected'] as bool? ?? _state.mt5Connected,
          ));
          break;
        case 'kill_switch':
          _update(_state.copyWith(
            killSwitchActive: data['active'] as bool? ?? _state.killSwitchActive,
            killSwitchReason: data['reason'] as String? ?? _state.killSwitchReason,
          ));
          break;
        case 'position_update':
          _update(_state.copyWith(
            currentPositions: data['count'] as int? ?? _state.currentPositions,
          ));
          break;
      }
    } catch (_) {}
  }

  // ── REST API calls ────────────────────────────────────────────────────────

  Future<void> _fetchStatus() async {
    try {
      final data = await _api.get('/api/v1/engine/status') as Map<String, dynamic>;
      final aiData = await _api.get('/api/v1/ai/thoughts') as Map<String, dynamic>;
      
      final mt5 = (data['mt5'] as Map<String, dynamic>?) ?? {};
      final acc = (mt5['account'] as Map<String, dynamic>?) ?? {};
      final risk = (data['risk'] as Map<String, dynamic>?) ?? {};
      final ks = (data['kill_switch'] as Map<String, dynamic>?) ?? {};
      final session = (data['session'] as Map<String, dynamic>?) ?? {};
      final market = (data['market'] as Map<String, dynamic>?) ?? {};

      _update(_state.copyWith(
        mt5Connected: mt5['connected'] as bool? ?? false,
        balance: (acc['balance'] as num?)?.toDouble() ?? 0,
        equity: (acc['equity'] as num?)?.toDouble() ?? 0,
        freeMargin: (acc['free_margin'] as num?)?.toDouble() ?? 0,
        dailyPnl: (risk['daily_pnl'] as num?)?.toDouble() ?? 0,
        dailyTrades: (risk['daily_trades'] as int?) ?? 0,
        killSwitchActive: ks['active'] as bool? ?? false,
        killSwitchReason: ks['reason'] as String? ?? '',
        session: session['session'] as String? ?? 'unknown',
        regime: market['regime'] as String? ?? mt5['regime'] as String? ?? 'TRENDING',
        agentThought: aiData['latest_thought'] as String? ?? 'Thinking...',
      ));
    } catch (e) {
      if (kDebugMode) print('EngineService._fetchStatus error: $e');
    }
  }

  Future<bool> activateKillSwitch(String reason) async {
    try {
      await _api.post('/api/v1/engine/kill', body: {'reason': reason});
      await _fetchStatus();
      return true;
    } catch (e) {
      if (kDebugMode) print('Kill switch error: $e');
      return false;
    }
  }

  Future<bool> deactivateKillSwitch(String reason) async {
    try {
      await _api.post('/api/v1/engine/unkill', body: {'reason': reason});
      await _fetchStatus();
      return true;
    } catch (e) {
      if (kDebugMode) print('Unkill error: $e');
      return false;
    }
  }

  Future<List<Map<String, dynamic>>> getOpenPositions() async {
    try {
      final data = await _api.get('/api/v1/trading/open-positions') as Map<String, dynamic>;
      return List<Map<String, dynamic>>.from(
        (data['positions'] ?? data['trades'] ?? []) as List
      );
    } catch (_) {
      return [];
    }
  }

  @override
  void dispose() {
    _disposed = true;
    _ws?.sink.close();
    _reconnectTimer?.cancel();
    _pollTimer?.cancel();
    super.dispose();
  }
}
