import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'services/api_config.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/trading_service.dart';
import 'services/ai_agent_service.dart';
import 'screens/login_screen.dart';
import 'screens/main_tab_screen.dart';

import 'package:firebase_core/firebase_core.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  
  await ApiConfig.init();
  
  final apiClient = ApiClient();
  await apiClient.init();

  runApp(
    MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: apiClient),
        ProxyProvider<ApiClient, AuthService>(
          update: (_, client, __) => AuthService(client),
        ),
        ProxyProvider<ApiClient, TradingService>(
          update: (_, client, __) => TradingService(client),
        ),
        ProxyProvider<ApiClient, AiAgentService>(
          update: (_, client, __) => AiAgentService(client),
        ),
      ],
      child: const VeloraApp(),
    ),
  );
}

class VeloraApp extends StatelessWidget {
  const VeloraApp({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context, listen: false);

    return MaterialApp(
      title: 'Velora',
      theme: VeloraTheme.darkTheme,
      debugShowCheckedModeBanner: false,
      home: authService.isLoggedIn ? const MainTabScreen() : const LoginScreen(),
    );
  }
}
