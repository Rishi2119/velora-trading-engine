import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_client.dart';
import '../theme.dart';

class BacktesterScreen extends StatefulWidget {
  const BacktesterScreen({super.key});

  @override
  State<BacktesterScreen> createState() => _BacktesterScreenState();
}

class _BacktesterScreenState extends State<BacktesterScreen> {
  final _formKey = GlobalKey<FormState>();
  String _symbol = 'EURUSD';
  String _timeframe = 'M15';
  int _days = 30;
  bool _loading = false;
  Map<String, dynamic>? _results;

  Future<void> _runBacktest() async {
    setState(() => _loading = true);
    try {
      final api = context.read<ApiClient>();
      final data = await api.post('/api/v1/backtest/run', body: {
        'symbol': _symbol,
        'timeframe': _timeframe,
        'days': _days,
        'strategy': 'EmaRsi_Trend',
      });
      setState(() => _results = data as Map<String, dynamic>);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: VeloraTheme.backgroundColor,
      appBar: AppBar(
        title: const Text('Backtester Engine', style: TextStyle(fontWeight: FontWeight.w800)),
        backgroundColor: VeloraTheme.surfaceColor,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildConfigCard(),
            const SizedBox(height: 16),
            if (_results != null) _buildResultsCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildConfigCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: VeloraTheme.surfaceColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Configuration', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 16),
            _buildLabel('Symbol'),
            TextFormField(
              initialValue: _symbol,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('e.g. BTCUSD'),
              onChanged: (v) => _symbol = v,
            ),
            const SizedBox(height: 12),
            _buildLabel('Timeframe'),
            DropdownButtonFormField<String>(
              value: _timeframe,
              dropdownColor: VeloraTheme.surfaceColor,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration(''),
              items: ['M1', 'M5', 'M15', 'H1', 'H4', 'D1'].map((tf) => 
                DropdownMenuItem(value: tf, child: Text(tf))).toList(),
              onChanged: (v) => setState(() => _timeframe = v!),
            ),
            const SizedBox(height: 12),
            _buildLabel('Lookback (Days)'),
            TextFormField(
              initialValue: _days.toString(),
              keyboardType: TextInputType.number,
              style: const TextStyle(color: Colors.white),
              decoration: _inputDecoration('30'),
              onChanged: (v) => _days = int.tryParse(v) ?? 30,
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _loading ? null : _runBacktest,
                style: ElevatedButton.styleFrom(
                  backgroundColor: VeloraTheme.primaryColor,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                child: _loading 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('RUN BACKTEST', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultsCard() {
    final roi = (_results?['roi_pct'] as num?)?.toDouble() ?? 0.0;
    final winRate = (_results?['win_rate_pct'] as num?)?.toDouble() ?? 0.0;
    final dd = (_results?['max_drawdown_pct'] as num?)?.toDouble() ?? 0.0;
    final sharpe = (_results?['sharpe_ratio'] as num?)?.toDouble() ?? 0.0;

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
          const Text('Verification Results', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
            childAspectRatio: 2,
            children: [
              _resultTile('ROI', '${roi.toStringAsFixed(2)}%', roi >= 0 ? Colors.green : Colors.red),
              _resultTile('Win Rate', '${winRate.toStringAsFixed(1)}%', Colors.cyanAccent),
              _resultTile('Max DD', '${dd.toStringAsFixed(2)}%', Colors.redAccent),
              _resultTile('Sharpe', sharpe.toStringAsFixed(2), Colors.purpleAccent),
            ],
          ),
          const SizedBox(height: 16),
          _resultTile('Total Trades', '${_results?['trades_count'] ?? 0}', Colors.white, large: true),
        ],
      ),
    );
  }

  Widget _resultTile(String label, String value, Color color, {bool large = false}) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(label, style: const TextStyle(color: Colors.white54, fontSize: 10)),
          Text(value, style: TextStyle(color: color, fontSize: large ? 18 : 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 6),
    child: Text(text, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
  );

  InputDecoration _inputDecoration(String hint) => InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: Colors.white24),
    filled: true,
    fillColor: Colors.white.withOpacity(0.03),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
  );
}
