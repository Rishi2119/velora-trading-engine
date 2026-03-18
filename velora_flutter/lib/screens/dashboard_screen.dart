import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/engine_service.dart';
import '../services/api_client.dart';
import '../theme.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  late EngineService _engine;
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _initialized = true;
      final apiClient = context.read<ApiClient>();
      _engine = EngineService(apiClient);
      _engine.init();
    }
  }

  @override
  void dispose() {
    _engine.dispose();
    super.dispose();
  }

  // ── Kill switch dialog ────────────────────────────────────────────────────

  Future<void> _showKillDialog() async {
    final state = _engine.state;
    if (state.killSwitchActive) {
      // Deactivate
      final ok = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: VeloraTheme.surfaceColor,
          title: const Text('Resume Trading?', style: TextStyle(color: Colors.white)),
          content: const Text(
            'This will deactivate the kill switch and allow new trades.',
            style: TextStyle(color: Colors.white60),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: VeloraTheme.successColor),
              child: const Text('Resume'),
            ),
          ],
        ),
      );
      if (ok == true) {
        await _engine.deactivateKillSwitch('Manual resume from mobile app');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Kill switch deactivated — engine resuming'), backgroundColor: Colors.green),
          );
        }
      }
    } else {
      // Activate
      final ok = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          backgroundColor: VeloraTheme.surfaceColor,
          title: const Text('⚠️ Activate Kill Switch?', style: TextStyle(color: Colors.white)),
          content: const Text(
            'ALL open positions will be closed immediately. Trading will halt until manually resumed.',
            style: TextStyle(color: Colors.white60),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
              child: const Text('KILL SWITCH'),
            ),
          ],
        ),
      );
      if (ok == true) {
        await _engine.activateKillSwitch('Manual kill from mobile app');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Kill switch activated — all positions closed'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return AnimatedBuilder(
      animation: _engine,
      builder: (context, _) {
        final s = _engine.state;
        return Scaffold(
          backgroundColor: VeloraTheme.backgroundColor,
          body: RefreshIndicator(
            onRefresh: _engine.init,
            color: VeloraTheme.primaryColor,
            child: CustomScrollView(
              slivers: [
                _buildAppBar(s),
                SliverPadding(
                  padding: const EdgeInsets.all(16),
                  sliver: SliverList(
                    delegate: SliverChildListDelegate([
                      // Kill Switch Banner
                      if (s.killSwitchActive)
                        _buildKillSwitchBanner(s),

                      const SizedBox(height: 8),

                      // Stats Grid
                      _buildStatsGrid(s),
                      const SizedBox(height: 16),

                      // Session / Filter
                      _buildSessionCard(s),
                      const SizedBox(height: 16),

                      // AI Agent Thought
                      _buildAgentCard(s),
                      const SizedBox(height: 16),

                      // Open Positions (lazy)
                      _buildPositionsCard(),
                    ]),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAppBar(EngineState s) {
    return SliverAppBar(
      backgroundColor: VeloraTheme.surfaceColor,
      floating: true,
      snap: true,
      title: Row(
        children: [
          const Text('Velora', style: TextStyle(fontWeight: FontWeight.w800, color: Colors.white)),
          const SizedBox(width: 8),
          // WS indicator
          Container(
            width: 8, height: 8,
            decoration: BoxDecoration(
              color: s.wsConnected ? Colors.green : Colors.orange,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: (s.wsConnected ? Colors.green : Colors.orange).withOpacity(0.5),
                  blurRadius: 6,
                ),
              ],
            ),
          ),
        ],
      ),
      actions: [
        // MT5 status chip
        Container(
          margin: const EdgeInsets.only(right: 8),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: s.mt5Connected
                ? Colors.green.withOpacity(0.15)
                : Colors.orange.withOpacity(0.15),
            borderRadius: BorderRadius.circular(100),
            border: Border.all(
              color: s.mt5Connected
                  ? Colors.green.withOpacity(0.4)
                  : Colors.orange.withOpacity(0.4),
            ),
          ),
          child: Text(
            s.mt5Connected ? 'MT5 Live' : 'Demo',
            style: TextStyle(
              color: s.mt5Connected ? Colors.green : Colors.orange,
              fontSize: 11, fontWeight: FontWeight.w600,
            ),
          ),
        ),
        // Kill Switch button
        IconButton(
          icon: Icon(
            s.killSwitchActive ? Icons.play_circle : Icons.power_settings_new,
            color: s.killSwitchActive ? Colors.green : Colors.red,
          ),
          tooltip: s.killSwitchActive ? 'Resume Engine' : 'Kill Switch',
          onPressed: _showKillDialog,
        ),
      ],
    );
  }

  Widget _buildKillSwitchBanner(EngineState s) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.1),
        border: Border.all(color: Colors.red.withOpacity(0.3)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Kill Switch Active',
                    style: TextStyle(color: Colors.red, fontWeight: FontWeight.w700, fontSize: 13)),
                if (s.killSwitchReason.isNotEmpty)
                  Text(s.killSwitchReason,
                      style: const TextStyle(color: Colors.white60, fontSize: 11)),
              ],
            ),
          ),
          TextButton(
            onPressed: _showKillDialog,
            child: const Text('Resume', style: TextStyle(color: Colors.green)),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid(EngineState s) {
    final items = [
      _StatItem('Balance', '\$${s.balance.toStringAsFixed(2)}', Icons.account_balance_wallet, Colors.white),
      _StatItem('Daily P&L',
        '${s.dailyPnl >= 0 ? "+" : ""}\$${s.dailyPnl.toStringAsFixed(2)}',
        Icons.trending_up,
        s.dailyPnl >= 0 ? Colors.green : Colors.red),
      _StatItem('Daily Trades', '${s.dailyTrades}', Icons.swap_horiz, VeloraTheme.primaryColor),
      _StatItem('Positions', '${s.currentPositions}', Icons.analytics, Colors.blue[300]!),
      _StatItem('Regime', s.regime.replaceAll('_', ' '), Icons.radar, Colors.purpleAccent),
    ];

    return GridView.count(
      crossAxisCount: 2,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.6,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: items.map(_buildStatCard).toList(),
    );
  }

  Widget _buildStatCard(_StatItem item) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: VeloraTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(item.label, style: const TextStyle(color: Colors.white60, fontSize: 11, fontWeight: FontWeight.w500)),
              Icon(item.icon, size: 14, color: Colors.white30),
            ],
          ),
          Text(item.value, style: TextStyle(color: item.color, fontSize: 20, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }

  Widget _buildSessionCard(EngineState s) {
    final isOpen = !['closed', 'unknown'].contains(s.session);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: VeloraTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Row(
        children: [
          Icon(
            isOpen ? Icons.check_circle : Icons.access_time,
            color: isOpen ? Colors.green : Colors.orange,
            size: 20,
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                isOpen ? 'Trading Session: ${s.session.toUpperCase()}' : 'Market Closed',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
              ),
              Text(
                isOpen ? 'Engine is actively monitoring' : 'Next: London Open 08:00 UTC',
                style: const TextStyle(color: Colors.white60, fontSize: 11),
              ),
            ],
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: isOpen ? Colors.green.withOpacity(0.15) : Colors.grey.withOpacity(0.15),
              borderRadius: BorderRadius.circular(100),
            ),
            child: Text(
              isOpen ? 'OPEN' : 'CLOSED',
              style: TextStyle(
                color: isOpen ? Colors.green : Colors.grey,
                fontSize: 11, fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAgentCard(EngineState s) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: VeloraTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.memory, color: Colors.cyanAccent, size: 20),
              const SizedBox(width: 12),
              const Text('Latest Agent Insights', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            s.agentThought.isEmpty ? 'No recent insights available.' : s.agentThought,
            style: const TextStyle(color: Colors.white70, fontSize: 12, height: 1.5, fontStyle: FontStyle.italic),
            maxLines: 4,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildPositionsCard() {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _engine.getOpenPositions(),
      builder: (context, snap) {
        final positions = snap.data ?? [];
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: VeloraTheme.surfaceColor,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: Colors.white.withOpacity(0.07)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Open Positions', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                  Text('${positions.length} positions',
                      style: const TextStyle(color: Colors.white60, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 12),
              if (positions.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('No open positions', style: TextStyle(color: Colors.white60)),
                  ),
                )
              else
                ...positions.map((p) => _buildPositionRow(p)),
            ],
          ),
        );
      },
    );
  }

  Widget _buildPositionRow(Map<String, dynamic> p) {
    final isBuy = (p['direction'] == 'BUY') || ((p['type'] as int?) == 0);
    final pnl = (p['profit'] ?? p['pnl'] ?? 0.0) as num;
    final symbol = (p['symbol'] ?? '') as String;
    final lots = p['volume'] ?? p['lots'] ?? 0;
    final comment = (p['comment'] ?? '') as String;
    final strategyName = comment.startsWith('Velora-Paper-')
        ? comment.replaceFirst('Velora-Paper-', '')
        : (comment.startsWith('Velora-')
            ? comment.replaceFirst('Velora-', '')
            : 'Manual');
            
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: isBuy ? Colors.green.withOpacity(0.15) : Colors.red.withOpacity(0.15),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              isBuy ? 'BUY' : 'SELL',
              style: TextStyle(
                color: isBuy ? Colors.green : Colors.red,
                fontSize: 11, fontWeight: FontWeight.w700,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(symbol, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                    const SizedBox(width: 6),
                    Text(strategyName, style: TextStyle(color: VeloraTheme.primaryColor.withOpacity(0.7), fontSize: 10, fontWeight: FontWeight.bold)),
                  ],
                ),
                Text('$lots lots • $comment', style: const TextStyle(color: Colors.white60, fontSize: 10)),
              ],
            ),
          ),
          Text(
            '${pnl >= 0 ? "+" : ""}\$${pnl.toStringAsFixed(2)}',
            style: TextStyle(
              color: pnl >= 0 ? Colors.green : Colors.red,
              fontWeight: FontWeight.w700, fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatItem {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  const _StatItem(this.label, this.value, this.icon, this.color);
}
