import 'package:material_ui/material_ui.dart';

import '../core/l10n_ext.dart';
import '../theme/tokens.dart';

const maxDreamLyceums = 3;

/// Ordered priority slots 1-2-3 with reorder up/down and remove, plus the admission rules.
class PriorityPicker extends StatelessWidget {
  const PriorityPicker({super.key, required this.ids, required this.nameOf, required this.onChanged});

  final List<String> ids;
  final String Function(String id) nameOf;
  final ValueChanged<List<String>> onChanged;

  void _move(int from, int to) {
    final next = [...ids];
    final id = next.removeAt(from);
    next.insert(to, id);
    onChanged(next);
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      for (var i = 0; i < maxDreamLyceums; i++)
        Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: i < ids.length ? Tokens.blueSoft : Colors.white,
            border: Border.all(color: i < ids.length ? Tokens.brand : Tokens.border, width: Tokens.borderWidth),
            borderRadius: BorderRadius.circular(Tokens.radius),
          ),
          child: Row(children: [
            CircleAvatar(
              radius: 14,
              backgroundColor: i < ids.length ? Tokens.brand : Tokens.border,
              foregroundColor: i < ids.length ? Colors.white : Tokens.textMuted,
              child: Text('${i + 1}', style: const TextStyle(fontWeight: FontWeight.w800)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                i < ids.length ? nameOf(ids[i]) : l.emptySlot,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontWeight: FontWeight.w800, color: i < ids.length ? Tokens.text : Tokens.textMuted),
              ),
            ),
            if (i < ids.length) ...[
              IconButton(
                tooltip: l.moveUp,
                icon: const Icon(Icons.arrow_upward_rounded),
                onPressed: i == 0 ? null : () => _move(i, i - 1),
              ),
              IconButton(
                tooltip: l.moveDown,
                icon: const Icon(Icons.arrow_downward_rounded),
                onPressed: i == ids.length - 1 ? null : () => _move(i, i + 1),
              ),
              IconButton(
                tooltip: l.removeItem,
                icon: const Icon(Icons.close_rounded),
                onPressed: () => onChanged([...ids]..removeAt(i)),
              ),
            ],
          ]),
        ),
      const SizedBox(height: 4),
      Text(l.dreamRules, style: const TextStyle(color: Tokens.textMuted, fontSize: 13, fontWeight: FontWeight.w700)),
    ]);
  }
}
