import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'chunky.dart';
import 'math_text.dart';

enum OptionStatus { idle, selected, correct, wrong }

class OptionTile extends StatelessWidget {
  const OptionTile({
    super.key,
    required this.text,
    required this.status,
    required this.onTap,
    this.hotkey,
  });

  final String text;
  final OptionStatus status;
  final VoidCallback? onTap;
  final String? hotkey;

  @override
  Widget build(BuildContext context) {
    final (face, edge, border, fg) = switch (status) {
      OptionStatus.selected => (Tokens.blueSoft, Tokens.blue, Tokens.blue, Tokens.blueText),
      OptionStatus.correct => (Tokens.greenSoft, Tokens.green, Tokens.green, Tokens.greenText),
      OptionStatus.wrong => (Tokens.redSoft, Tokens.red, Tokens.red, Tokens.redEdge),
      OptionStatus.idle => (Colors.white, Tokens.border, Tokens.border, Tokens.text),
    };
    return Semantics(
      button: true,
      enabled: onTap != null,
      selected: status == OptionStatus.selected,
      label: [if (hotkey != null) hotkey!, text].join('. '),
      excludeSemantics: true,
      onTap: onTap,
      child: PressableChunky(
        onPressed: onTap,
        builder: (_, pressed) => Chunky(
          face: face,
          edge: edge,
          borderColor: border,
          pressed: pressed,
          child: Row(
            children: [
              if (hotkey != null)
                Container(
                  width: 28,
                  height: 28,
                  alignment: Alignment.center,
                  margin: const EdgeInsets.only(right: 12),
                  decoration: BoxDecoration(
                    border: Border.all(color: border, width: Tokens.borderWidth),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(hotkey!, style: TextStyle(color: fg, fontWeight: FontWeight.w800)),
                ),
              Expanded(child: MathText(text, style: TextStyle(color: fg, fontSize: 16, fontWeight: FontWeight.w700))),
              if (status == OptionStatus.correct) Icon(Icons.check_circle_rounded, color: fg),
              if (status == OptionStatus.wrong) Icon(Icons.cancel_rounded, color: fg),
            ],
          ),
        ),
      ),
    );
  }
}
