import 'package:flutter/material.dart';

import '../core/models.dart';
import '../theme/tokens.dart';
import 'chunky.dart';

enum NodeState { done, current, open, locked }

/// Round lesson node on the Learn path; the state comes from the lesson's
/// `progress.state` (locked nodes are inert).
class PathNode extends StatelessWidget {
  const PathNode({super.key, required this.lesson, required this.onTap, this.state = NodeState.open, this.size = 72});
  final PathLesson lesson;
  final VoidCallback onTap;
  final NodeState state;
  final double size;

  @override
  Widget build(BuildContext context) {
    final (face, edge, icon) = switch (state) {
      NodeState.done => (Tokens.gold, Tokens.goldEdge, Icons.check_rounded),
      NodeState.current => (Tokens.brand, Tokens.brandEdge, Icons.star_rounded),
      NodeState.open => (Tokens.brand, Tokens.brandEdge, lesson.legendary ? Icons.workspace_premium_rounded : Icons.play_arrow_rounded),
      NodeState.locked => (Tokens.border, Tokens.lockedEdge, Icons.lock_rounded),
    };
    final iconColor = switch (state) {
      NodeState.done => Tokens.onGold,
      NodeState.locked => Tokens.lockedEdge,
      _ => Colors.white,
    };
    final onTap = state == NodeState.locked ? () {} : this.onTap;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Semantics(
          button: true,
          label: lesson.title,
          excludeSemantics: true,
          onTap: onTap,
          child: PressableChunky(
            onPressed: onTap,
            builder: (_, pressed) => SizedBox(
              width: size,
              child: Chunky(
                face: face,
                edge: edge,
                pressed: pressed,
                radius: size,
                padding: EdgeInsets.symmetric(vertical: (size - 36) / 2 - 4),
                child: Icon(icon, color: iconColor, size: 36),
              ),
            ),
          ),
        ),
        const SizedBox(height: 4),
        SizedBox(
          width: 110,
          child: Text(
            lesson.title,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 12),
          ),
        ),
      ],
    );
  }
}
