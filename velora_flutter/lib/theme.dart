import 'package:flutter/material.dart';

class AppTheme {
  // Brand
  static const Color primary = Color(0xFF6366f1);
  static const Color secondary = Color(0xFF8b5cf6);
  static const Color accent = Color(0xFF06b6d4);

  // Background layers
  static const Color bgBase = Color(0xFF0a0b0e);
  static const Color bgSurface = Color(0xFF111318);
  static const Color bgCard = Color(0xFF161921);
  static const Color bgElevated = Color(0xFF1d2029);

  // Text
  static const Color textPrimary = Color(0xFFf1f2f6);
  static const Color textSecondary = Color(0xFF8b8fa8);
  static const Color textMuted = Color(0xFF4a4d5e);

  // Status
  static const Color success = Color(0xFF10b981);
  static const Color error = Color(0xFFef4444);
  static const Color warning = Color(0xFFf59e0b);

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      primaryColor: primary,
      scaffoldBackgroundColor: bgBase,
      cardColor: bgCard,
      colorScheme: const ColorScheme.dark(
        primary: primary,
        secondary: secondary,
        surface: bgSurface,
        background: bgBase,
        error: error,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: bgSurface,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
        ),
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(color: textPrimary, fontSize: 32, fontWeight: FontWeight.bold),
        titleLarge: TextStyle(color: textPrimary, fontSize: 20, fontWeight: FontWeight.w600),
        bodyLarge: TextStyle(color: textPrimary, fontSize: 16),
        bodyMedium: TextStyle(color: textSecondary, fontSize: 14),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: Colors.white,
          elevation: 4,
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: bgElevated,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: Colors.white.withOpacity(0.07)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: Colors.white.withOpacity(0.07)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: primary, width: 2),
        ),
        hintStyle: const TextStyle(color: textMuted),
        labelStyle: const TextStyle(color: textSecondary),
      ),
    );
  }
}
