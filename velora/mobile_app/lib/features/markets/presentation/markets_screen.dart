import 'package:flutter/material.dart';

class MarketsScreen extends StatelessWidget {
  const MarketsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final pairs = const [
      ('EUR/USD', '+0.42%'),
      ('GBP/USD', '-0.17%'),
      ('XAU/USD', '+1.08%'),
      ('BTC/USDT', '+2.91%'),
    ];

    return SafeArea(
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: pairs.length,
        itemBuilder: (context, index) {
          final item = pairs[index];
          final positive = item.$2.startsWith('+');
          return Card(
            child: ListTile(
              title: Text(item.$1),
              subtitle: const Text('Tap to open depth + chart'),
              trailing: Text(
                item.$2,
                style: TextStyle(color: positive ? const Color(0xFF00FF9F) : const Color(0xFFFF4D4D)),
              ),
            ),
          );
        },
      ),
    );
  }
}
