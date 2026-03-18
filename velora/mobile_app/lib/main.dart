import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:velora_trade_terminal/core/services/supabase_service.dart';
import 'package:velora_trade_terminal/core/theme/app_theme.dart';
import 'package:velora_trade_terminal/features/auth/presentation/auth_gate.dart';
import 'package:velora_trade_terminal/features/dashboard/presentation/dashboard_screen.dart';
import 'package:velora_trade_terminal/features/journal/presentation/journal_screen.dart';
import 'package:velora_trade_terminal/features/markets/presentation/markets_screen.dart';
import 'package:velora_trade_terminal/features/profile/presentation/profile_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SupabaseService.initialize();
  runApp(const ProviderScope(child: VeloraApp()));
}

class VeloraApp extends StatelessWidget {
  const VeloraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Velora Trade Terminal',
      theme: AppTheme.dark(),
      home: const AuthGate(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class TerminalShell extends StatefulWidget {
  const TerminalShell({super.key});

  @override
  State<TerminalShell> createState() => _TerminalShellState();
}

class _TerminalShellState extends State<TerminalShell> {
  int _index = 0;

  final _pages = const [
    DashboardScreen(),
    MarketsScreen(),
    JournalScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _pages[_index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.show_chart), label: 'Markets'),
          NavigationDestination(icon: Icon(Icons.menu_book_outlined), label: 'Journal'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Profile'),
        ],
      ),
    );
  }
}
