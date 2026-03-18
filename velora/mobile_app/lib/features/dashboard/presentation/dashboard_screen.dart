import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:velora_trade_terminal/core/theme/app_theme.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Good session, trader.', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 6),
          Text('Discipline beats emotion.', style: Theme.of(context).textTheme.bodyMedium),
          const SizedBox(height: 16),
          Row(
            children: const [
              Expanded(child: _StatCard(title: 'Portfolio', value: '\$128,420.14', color: AppTheme.electricBlue)),
              SizedBox(width: 12),
              Expanded(child: _StatCard(title: 'PnL Today', value: '+2.43%', color: AppTheme.profit)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: const [
              Expanded(child: _StatCard(title: 'Daily Streak', value: '14 days', color: AppTheme.premium)),
              SizedBox(width: 12),
              Expanded(child: _StatCard(title: 'Discipline', value: '89/100', color: AppTheme.profit)),
            ],
          ),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(height: 180, child: LineChart(_chartData())),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Achievements', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: const [
                      Chip(label: Text('No Overtrading')),
                      Chip(label: Text('Risk Master')),
                      Chip(label: Text('Journal Consistency')),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: FilledButton(
                  onPressed: () {},
                  child: const Text('Buy'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: FilledButton.tonal(
                  onPressed: () {},
                  child: const Text('Sell'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton(
                  onPressed: () {},
                  child: const Text('Analyze'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  LineChartData _chartData() {
    return LineChartData(
      gridData: const FlGridData(show: false),
      borderData: FlBorderData(show: false),
      titlesData: const FlTitlesData(show: false),
      lineBarsData: [
        LineChartBarData(
          isCurved: true,
          barWidth: 3,
          color: AppTheme.profit,
          spots: const [
            FlSpot(0, 1),
            FlSpot(1, 1.5),
            FlSpot(2, 1.2),
            FlSpot(3, 2.1),
            FlSpot(4, 2.4),
            FlSpot(5, 3),
          ],
          dotData: const FlDotData(show: false),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.title, required this.value, required this.color});

  final String title;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            Text(value, style: Theme.of(context).textTheme.titleLarge?.copyWith(color: color)),
          ],
        ),
      ),
    );
  }
}
