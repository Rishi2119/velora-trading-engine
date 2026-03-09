import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiConfig {
  /// Defines the possible environments
  static const bool isProduction = kReleaseMode;
  
  /// Base URL for Production (uses env var or fallback)
  static String get _productionUrl => dotenv.env['API_BASE_URL'] ?? 'https://api.velora.com/api/v1';

  /// Custom LAN IP for testing on physical devices (loaded from .env if available)
  static String get _lanIp => dotenv.env['LOCAL_NETWORK_IP'] ?? ''; 
  
  /// Port for the backend - Use 8000 for FastAPI (unified API with auth)
  static const String _port = '8000';

  /// Determine the base URL dynamically based on environment and platform
  static String get baseUrl {
    if (isProduction) {
      return _productionUrl;
    }

    // Web uses localhost
    if (kIsWeb) {
      return 'http://localhost:$_port/api/v1';
    }

    // If LOCAL_NETWORK_IP is defined in .env, use it (works for physical devices on same WiFi)
    if (_lanIp.isNotEmpty) {
      return 'http://$_lanIp:$_port/api/v1';
    }

    // Auto-detect Localhost based on platform
    if (defaultTargetPlatform == TargetPlatform.android) {
      // Android Emulator maps 10.0.2.2 to the host machine's localhost
      return 'http://10.0.2.2:$_port/api/v1';
    } else if (defaultTargetPlatform == TargetPlatform.iOS || defaultTargetPlatform == TargetPlatform.macOS) {
      // iOS Simulator can access host machine's localhost directly
      return 'http://localhost:$_port/api/v1';
    } else {
      // Fallback for Desktop
      return 'http://127.0.0.1:$_port/api/v1';
    }
  }

  /// Initialize environment config (load .env)
  static Future<void> init() async {
    try {
      await dotenv.load(fileName: ".env");
    } catch (e) {
      debugPrint("No .env file found. Proceeding with default ApiConfig.");
    }
    
    debugPrint("=== Network Config ===");
    debugPrint("Is Production: $isProduction");
    debugPrint("Is Web: $kIsWeb");
    debugPrint("Target Platform: $defaultTargetPlatform");
    debugPrint("Selected Base URL: $baseUrl");
    debugPrint("======================");
  }
}
