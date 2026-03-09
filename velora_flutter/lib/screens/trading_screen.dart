import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../services/trading_service.dart';
import '../theme.dart';

class TradingScreen extends StatefulWidget {
  const TradingScreen({super.key});

  @override
  State<TradingScreen> createState() => _TradingScreenState();
}

class _TradingScreenState extends State<TradingScreen> {
  List<dynamic> _positions = [];
  bool _loading = true;
  bool _killSwitchActive = false;
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
      final api = Provider.of<TradingService>(context, listen: false);
      final posData = await api.getOpenPositions();
      final statsData = await api.getStats();
      
      if (mounted) {
        setState(() {
          _positions = posData['trades'] ?? [];
          _killSwitchActive = statsData['kill_switch_active'] ?? false;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggleKillSwitch() async {
    try {
      final api = Provider.of<TradingService>(context, listen: false);
      // Optimistic update
      setState(() => _killSwitchActive = !_killSwitchActive);
      await api.toggleKillSwitch(_killSwitchActive);
    } catch (e) {
      // Revert on failure
      setState(() => _killSwitchActive = !_killSwitchActive);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to alter Kill Switch: $e')));
    }
  }

  Widget _buildPositionCard(Map<String, dynamic> trade) {
    final bool isBuy = trade['direction'].toString().toUpperCase().contains('BUY');
    final double pnl = (trade['pnl'] ?? 0).toDouble();

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Text(
                    trade['symbol'] ?? 'UNKNOWN',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: isBuy ? AppTheme.success.withOpacity(0.2) : AppTheme.error.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      trade['direction'],
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: isBuy ? AppTheme.success : AppTheme.error,
                      ),
                    ),
                  )
                ],
              ),
              Text(
                '${pnl >= 0 ? '+' : ''}\$${pnl.toStringAsFixed(2)}',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: pnl >= 0 ? AppTheme.success : AppTheme.error,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('ENTRY', style: TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold)),
                  Text('${trade['entry']}', style: const TextStyle(color: AppTheme.textSecondary, fontFamily: 'monospace')),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const Text('LOTS', style: TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold)),
                  Text('${trade['lots']}', style: const TextStyle(color: AppTheme.textSecondary, fontFamily: 'monospace')),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text('STATUS', style: TextStyle(color: AppTheme.textMuted, fontSize: 10, fontWeight: FontWeight.bold)),
                  Text('${trade['status']}', style: const TextStyle(color: AppTheme.primary, fontWeight: FontWeight.bold)),
                ],
              ),
            ],
          )
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _positions.isEmpty) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trading Execution'),
        actions: [
          IconButton(
            icon: Icon(
              _killSwitchActive ? LucideIcons.powerOff : LucideIcons.power, 
              color: _killSwitchActive ? AppTheme.error : AppTheme.textPrimary,
            ),
            onPressed: () => showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                backgroundColor: AppTheme.bgSurface,
                title: const Text('Confirm Kill Switch'),
                content: Text(
                  _killSwitchActive 
                    ? 'Deactivate the Kill Switch? Automated trading will resume immediately.'
                    : 'Activate Kill Switch? This will HALT all algorithmic trading and prevent new orders.'
                ),
                actions: [
                  TextButton(
                    child: const Text('Cancel', style: TextStyle(color: AppTheme.textSecondary)),
                    onPressed: () => Navigator.of(ctx).pop(),
                  ),
                  ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _killSwitchActive ? AppTheme.primary : AppTheme.error,
                    ),
                    onPressed: () {
                      Navigator.of(ctx).pop();
                      _toggleKillSwitch();
                    },
                    child: Text(_killSwitchActive ? 'DEACTIVATE' : 'ACTIVATE'),
                  )
                ],
              ),
            ),
          )
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchData,
        child: _positions.isEmpty 
          ? ListView(
              children: const [
                 SizedBox(height: 100),
                 Center(child: Text('No open positions.', style: TextStyle(color: AppTheme.textMuted)))
              ]
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _positions.length,
              itemBuilder: (context, index) {
                return _buildPositionCard(_positions[index]);
              },
            ),
      ),
    );
  }
}
