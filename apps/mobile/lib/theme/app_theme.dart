import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'tokens.dart';

ThemeData buildAppTheme() {
  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: Tokens.green,
      primary: Tokens.green,
      secondary: Tokens.blue,
      error: Tokens.red,
      surface: Tokens.surface,
    ),
    scaffoldBackgroundColor: Tokens.surface,
  );
  final text = GoogleFonts.nunitoTextTheme(base.textTheme).apply(
    bodyColor: Tokens.text,
    displayColor: Tokens.text,
  );
  TextStyle? bold(TextStyle? s, FontWeight w) => s?.copyWith(fontWeight: w);
  return base.copyWith(
    textTheme: text.copyWith(
      headlineMedium: bold(text.headlineMedium, FontWeight.w800),
      titleLarge: bold(text.titleLarge, FontWeight.w800),
      titleMedium: bold(text.titleMedium, FontWeight.w800),
      bodyLarge: bold(text.bodyLarge, FontWeight.w700),
      bodyMedium: bold(text.bodyMedium, FontWeight.w700),
      labelLarge: bold(text.labelLarge, FontWeight.w800),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: Tokens.surface,
      foregroundColor: Tokens.text,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: GoogleFonts.nunito(
        fontSize: 20,
        fontWeight: FontWeight.w800,
        color: Tokens.text,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: const Color(0xFFF7F7F7),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radius),
        borderSide: const BorderSide(color: Tokens.border, width: Tokens.borderWidth),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radius),
        borderSide: const BorderSide(color: Tokens.border, width: Tokens.borderWidth),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(Tokens.radius),
        borderSide: const BorderSide(color: Tokens.blue, width: Tokens.borderWidth),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Tokens.surface,
      indicatorColor: Tokens.blueSoft,
      surfaceTintColor: Colors.transparent,
      labelTextStyle: WidgetStatePropertyAll(
        GoogleFonts.nunito(fontSize: 11, fontWeight: FontWeight.w800, color: Tokens.text),
      ),
    ),
    dividerTheme: const DividerThemeData(color: Tokens.border, thickness: 2),
  );
}
