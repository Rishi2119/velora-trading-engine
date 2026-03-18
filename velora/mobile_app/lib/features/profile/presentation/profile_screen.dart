import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:velora_trade_terminal/features/subscription/presentation/subscription_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = Supabase.instance.client.auth.currentUser;
    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Profile', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 10),
          Card(
            child: ListTile(
              title: Text(user?.email ?? 'Unknown user'),
              subtitle: const Text('Risk profile: Moderate'),
            ),
          ),
          const SizedBox(height: 10),
          FilledButton.tonal(
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const SubscriptionScreen()),
              );
            },
            child: const Text('Manage Subscription'),
          ),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: () async {
              await Supabase.instance.client.auth.signOut();
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }
}
