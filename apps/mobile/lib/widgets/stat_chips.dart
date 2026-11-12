import 'package:material_ui/material_ui.dart';

import '../core/models.dart';
import '../theme/tokens.dart';

class StatChip extends StatelessWidget {
  const StatChip({super.key, required this.icon, required this.value, required this.color, this.label});
  final IconData icon;
  final String value;
  final Color color;
  final String? label;

  @override
  Widget build(BuildContext context) => Semantics(
        label: label == null ? value : '$label $value',
        excludeSemantics: true,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(width: 4),
            Text(value, style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 16)),
          ],
        ),
      );
}

/// Streak, gems and hearts row shown in app bars.
class StatChips extends StatelessWidget {
  const StatChips({super.key, required this.stats});
  final Stats stats;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          StatChip(icon: Icons.local_fire_department, value: '${stats.streak}', color: Tokens.orange),
          const SizedBox(width: 12),
          StatChip(icon: Icons.diamond, value: '${stats.gems}', color: Tokens.blueText),
          const SizedBox(width: 12),
          StatChip(
            icon: Icons.favorite,
            value: stats.hearts.unlimited ? '∞' : '${stats.hearts.count}',
            color: Tokens.redEdge,
          ),
          const SizedBox(width: 8),
        ],
      );
}
