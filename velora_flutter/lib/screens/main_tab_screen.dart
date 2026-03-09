import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'dashboard_screen.dart';
import 'trading_screen.dart';
import 'ai_agent_screen.dart';
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
      body: _screens[_currentIndex],
      bottomNavigationBar: BottomNavigationBar(
        backgroundColor: AppTheme.bgSurface,
        selectedItemColor: AppTheme.primary,
        unselectedItemColor: AppTheme.textSecondary,
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
}
