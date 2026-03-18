import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const background = Color(0xFF0A0F1C);
  static const card = Color(0xFF121826);
  static const profit = Color(0xFF00FF9F);
  static const loss = Color(0xFFFF4D4D);
  static const premium = Color(0xFFFFD700);
  static const electricBlue = Color(0xFF3A86FF);

  static ThemeData dark() {
    final textTheme = GoogleFonts.spaceGroteskTextTheme(
      ThemeData.dark().textTheme,
    );

    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: background,
      textTheme: textTheme,
      colorScheme: const ColorScheme.dark(
        primary: electricBlue,
        secondary: profit,
        surface: card,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: background,
        elevation: 0,
      ),
      cardTheme: CardTheme(
        color: card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: card,
        contentTextStyle: textTheme.bodyMedium,
      ),
    );
  }
}
