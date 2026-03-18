import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'dashboard_screen.dart';
import 'trading_screen.dart';
import 'ai_agent_screen.dart';
import 'backtester_screen.dart';
import 'accounts_screen.dart';
import 'copy_trading_screen.dart';
import '../theme.dart';

class MainTabScreen extends StatefulWidget {
  const MainTabScreen({super.key});

  @override
  State<MainTabScreen> createState() => _MainTabScreenState();
}

class _MainTabScreenState extends State<MainTabScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const DashboardScreen(),
    const TradingScreen(),
    const AiAgentScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _currentIndex == 0 ? null : AppBar(
        backgroundColor: VeloraTheme.surfaceColor,
        elevation: 0,
        title: Text(_currentIndex == 1 ? 'Trade' : 'AI Agent', style: const TextStyle(fontWeight: FontWeight.bold)),
      ),
      drawer: _buildDrawer(),
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: VeloraTheme.surfaceColor,
        selectedItemColor: VeloraTheme.primaryColor,
        unselectedItemColor: Colors.white38,
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.layoutDashboard),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.trendingUp),
            label: 'Trade',
          ),
          BottomNavigationBarItem(
            icon: Icon(LucideIcons.brain),
            label: 'AI Agent',
          ),
        ],
      ),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      backgroundColor: VeloraTheme.backgroundColor,
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: BoxDecoration(color: VeloraTheme.surfaceColor),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const Text('Velora', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900)),
                const Text('Institutional AI Engine', style: TextStyle(color: Colors.white38, fontSize: 12)),
                const SizedBox(height: 10),
              ],
            ),
          ),
          _drawerItem(LucideIcons.user, 'MT5 Accounts', () {
            Navigator.pop(context);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const AccountsScreen()));
          }),
          _drawerItem(LucideIcons.play, 'Backtester', () {
            Navigator.pop(context);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const BacktesterScreen()));
          }),
          _drawerItem(LucideIcons.copy, 'Copy Trading', () {
            Navigator.pop(context);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const CopyTradingScreen()));
          }),
          const Divider(color: Colors.white10),
          _drawerItem(LucideIcons.settings, 'Settings', () {}),
          _drawerItem(LucideIcons.logOut, 'Logout', () {
            Navigator.pop(context);
          }),
        ],
      ),
    );
  }

  Widget _drawerItem(IconData icon, String title, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: Colors.white70, size: 20),
      title: Text(title, style: const TextStyle(color: Colors.white, fontSize: 14)),
      onTap: onTap,
    );
  }
}
