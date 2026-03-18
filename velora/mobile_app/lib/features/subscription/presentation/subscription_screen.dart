import 'package:flutter/material.dart';

class SubscriptionScreen extends StatelessWidget {
  const SubscriptionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Subscription Plans')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          _PlanCard(
            title: 'Free',
            price: '\$0/mo',
            features: ['Basic dashboard', 'Limited journal history'],
          ),
          SizedBox(height: 12),
          _PlanCard(
            title: 'Pro',
            price: '\$29/mo',
            features: ['Advanced analytics', 'Unlimited journal', 'Priority support'],
          ),
          SizedBox(height: 12),
          _PlanCard(
            title: 'Premium',
            price: '\$99/mo',
            features: ['AI trade insights', 'Performance coaching', 'Team trading rooms'],
          ),
        ],
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({required this.title, required this.price, required this.features});

  final String title;
  final String price;
  final List<String> features;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 6),
            Text(price, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            ...features.map((feature) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Text('- $feature'),
                )),
            const SizedBox(height: 10),
            FilledButton(onPressed: null, child: Text('Current / Upgrade')),
          ],
        ),
      ),
    );
  }
}
