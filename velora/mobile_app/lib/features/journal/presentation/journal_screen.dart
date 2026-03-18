import 'package:flutter/material.dart';

class JournalScreen extends StatefulWidget {
  const JournalScreen({super.key});

  @override
  State<JournalScreen> createState() => _JournalScreenState();
}

class _JournalScreenState extends State<JournalScreen> {
  final _pairController = TextEditingController();
  final _noteController = TextEditingController();
  final _emotionController = TextEditingController();

  @override
  void dispose() {
    _pairController.dispose();
    _noteController.dispose();
    _emotionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Trading Journal', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 12),
          TextField(
            controller: _pairController,
            decoration: const InputDecoration(labelText: 'Pair (e.g. EUR/USD)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _emotionController,
            decoration: const InputDecoration(labelText: 'Emotion (calm, FOMO, fear)'),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _noteController,
            maxLines: 4,
            decoration: const InputDecoration(labelText: 'Trade Notes'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Journal entry saved.')),
              );
            },
            child: const Text('Save Entry'),
          ),
          const SizedBox(height: 16),
          const Card(
            child: ListTile(
              title: Text('Last insight'),
              subtitle: Text('You followed risk limits in 6/7 recent sessions.'),
            ),
          ),
        ],
      ),
    );
  }
}
