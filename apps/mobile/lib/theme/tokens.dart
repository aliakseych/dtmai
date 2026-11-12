import 'package:material_ui/material_ui.dart';

/// Duolingo-style design tokens. Brand: #100FA0 primary, #AFF50B accent, otherwise black & white.
/// `blue*` tokens are the primary (brand) shades; `green*` are the lime accent / success shades.
class Tokens {
  static const green = Color(0xFFAFF50B);
  static const greenEdge = Color(0xFF7FB800);
  static const greenSoft = Color(0xFFF1FDD0);
  static const blue = Color(0xFF100FA0);
  static const blueEdge = Color(0xFF0B0A78);
  static const blueSoft = Color(0xFFECECFF);
  static const red = Color(0xFFFF4B4B);
  static const redEdge = Color(0xFFEA2B2B);
  static const redSoft = Color(0xFFFFDFE0);
  static const gold = Color(0xFFFFC800);
  static const goldEdge = Color(0xFFE5B400);
  static const orange = Color(0xFFFF9600);
  static const brand = Color(0xFF100FA0);
  static const brandEdge = Color(0xFF0B0A78);
  static const accent = Color(0xFFAFF50B);
  static const text = Color(0xFF111111);
  static const textMuted = Color(0xFF6B6B6B);

  /// Dark text for gold surfaces (white on gold fails contrast).
  static const onGold = Color(0xFF4B3A00);

  /// Gold used as text on white.
  static const goldText = Color(0xFF8A6500);

  /// Green used as text on white (#58a700 meets contrast; #58cc02 does not).
  static const greenText = Color(0xFF3F5F00);

  /// Blue used as text on white.
  static const blueText = Color(0xFF100FA0);
  static const border = Color(0xFFE5E5E5);
  static const surface = Color(0xFFFFFFFF);
  static const locked = Color(0xFFE5E5E5);
  static const lockedEdge = Color(0xFFCECECE);

  static const radius = 16.0;
  static const edge = 4.0;
  static const borderWidth = 2.0;
}
