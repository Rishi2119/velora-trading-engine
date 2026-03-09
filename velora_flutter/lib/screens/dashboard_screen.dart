import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../services/auth_service.dart';
import '../services/trading_service.dart';
import '../services/ai_agent_service.dart';
import '../theme.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _stats;
  Map<String, dynamic>? _agent;
  bool _loading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchData();
    _timer = Timer.periodic(const Duration(seconds: 5), (_) => _fetchData());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchData() async {
    try {
      final tradingApi = Provider.of<TradingService>(context, listen: false);
      final aiApi = Provider.of<AiAgentService>(context, listen: false);
      final statsData = await tradingApi.getStats();
      final agentData = await aiApi.getAgentStatus();
      
      if (mounted) {
        setState(() {
          _stats = statsData;
          _agent = agentData;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Widget _buildStatCard(String title, String value, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
              Icon(icon, color: AppTheme.textSecondary, size: 16),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            value,
            style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _stats == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final balance = _stats?['account_balance'] ?? 0.0;
    final pnl = _stats?['total_pnl'] ?? 0.0;
    final winRate = _stats?['win_rate'] ?? 0.0;
    final openCount = _stats?['open_trades_count'] ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(icon: const Icon(LucideIcons.logOut), onPressed: () async {
             await Provider.of<AuthService>(context, listen: false).logout();
             if (context.mounted) Navigator.of(context).pushReplacementNamed('/'); 
          })
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // MT5 Status Bar
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: (_stats?['mt5_connected'] == true) 
                      ? AppTheme.success.withOpacity(0.1) 
                      : AppTheme.warning.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      LucideIcons.activity, 
                      color: (_stats?['mt5_connected'] == true) ? AppTheme.success : AppTheme.warning,
                      size: 16,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      (_stats?['mt5_connected'] == true) ? 'MT5 Connected (Live)' : 'MT5 Disconnected (Demo Mode)',
                      style: TextStyle(
                        color: (_stats?['mt5_connected'] == true) ? AppTheme.success : AppTheme.warning,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Grid 2x2
              Row(
                children: [
                  Expanded(child: _buildStatCard('Balance', '\$${balance.toStringAsFixed(2)}', AppTheme.textPrimary, LucideIcons.dollarSign)),
                  const SizedBox(width: 16),
                  Expanded(child: _buildStatCard('Total P&L', '${pnl >= 0 ? '+' : ''}\$${pnl.toStringAsFixed(2)}', pnl >= 0 ? AppTheme.success : AppTheme.error, LucideIcons.trendingUp)),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(child: _buildStatCard('Win Rate', '${winRate.toStringAsFixed(1)}%', AppTheme.primary, LucideIcons.target)),
                  const SizedBox(width: 16),
                  Expanded(child: _buildStatCard('Open Pos', '$openCount', AppTheme.textPrimary, LucideIcons.briefcase)),
                ],
              ),
              
              const SizedBox(height: 32),
              const Text('AI Agent Status', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.bgCard,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            const Icon(LucideIcons.brain, color: AppTheme.primary),
                            const SizedBox(width: 8),
                            Text(
                              (_agent?['is_running'] == true) ? 'Active' : 'Stopped',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                          ],
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: (_agent?['latest_decision'] == 'TRADE' || _agent?['latest_decision']?.contains('BUY') == true) 
                                ? AppTheme.success.withOpacity(0.2) 
                                : AppTheme.bgElevated,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            _agent?['latest_decision'] ?? 'HOLD',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: (_agent?['latest_decision'] == 'TRADE' || _agent?['latest_decision']?.contains('BUY') == true) 
                                  ? AppTheme.success 
                                  : AppTheme.textSecondary,
                            ),
                          ),
                        )
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      _agent?['latest_thought'] ?? 'Waiting for signals...',
                      style: const TextStyle(color: AppTheme.textSecondary, height: 1.5),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
