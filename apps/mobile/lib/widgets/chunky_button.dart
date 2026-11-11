import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'chunky.dart';

enum ChunkyTone { green, blue, red, gold, white }

class ChunkyButton extends StatelessWidget {
  const ChunkyButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.tone = ChunkyTone.green,
    this.expand = true,
    this.loading = false,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final ChunkyTone tone;
  final bool expand;
  final bool loading;
  final IconData? icon;

  (Color, Color, Color) get _colors {
    switch (tone) {
      case ChunkyTone.blue:
        return (Tokens.blue, Tokens.blueEdge, Colors.white);
      case ChunkyTone.red:
        return (Tokens.red, Tokens.redEdge, Colors.white);
      case ChunkyTone.gold:
        return (Tokens.gold, Tokens.goldEdge, Tokens.onGold);
      case ChunkyTone.white:
        return (Colors.white, Tokens.border, Tokens.blueText);
      case ChunkyTone.green:
        return (Tokens.brand, Tokens.brandEdge, Colors.white);
    }
  }

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null && !loading;
    final (face, edge, fg) = enabled ? _colors : (Tokens.border, Tokens.lockedEdge, Tokens.textMuted);
    return Semantics(
      button: true,
      enabled: enabled,
      label: label,
      excludeSemantics: true,
      child: PressableChunky(
      onPressed: enabled ? onPressed : null,
      builder: (_, pressed) => Chunky(
        face: face,
        edge: edge,
        pressed: pressed,
        borderColor: tone == ChunkyTone.white && enabled ? Tokens.border : null,
        child: Row(
          mainAxisSize: expand ? MainAxisSize.max : MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (loading)
              SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 3, color: fg),
              )
            else ...[
              if (icon != null) ...[Icon(icon, color: fg, size: 20), const SizedBox(width: 8)],
              Flexible(
                child: Text(
                  label.toUpperCase(),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: fg, fontWeight: FontWeight.w800, fontSize: 15, letterSpacing: 0.8),
                ),
              ),
            ],
          ],
        ),
      ),
    ),
    );
  }
}
