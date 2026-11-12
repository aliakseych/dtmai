import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import 'quest_providers.dart';

/// Daily quests. Rewards are granted automatically by the server when a quest completes.
class QuestsScreen extends ConsumerWidget {
  const QuestsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final tag = context.localeTag;
    final quests = ref.watch(questsProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.dailyQuests)),
      body: AsyncView<List<Quest>>(
        value: quests,
        isEmpty: (d) => d.isEmpty,
        onRetry: () => ref.invalidate(questsProvider),
        builder: (list) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(questsProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              for (final q in list)
                Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
                    borderRadius: BorderRadius.circular(Tokens.radius),
                  ),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Expanded(child: Text(pickName(q.title, tag), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                      if (q.completed) const Icon(Icons.check_circle_rounded, color: Tokens.greenEdge),
                      if (q.rewardXp > 0) Text(' +${q.rewardXp} ${l.xp}', style: const TextStyle(color: Tokens.goldText, fontWeight: FontWeight.w800)),
                      if (q.rewardGems > 0) ...[
                        const SizedBox(width: 8),
                        const Icon(Icons.diamond, color: Tokens.blue, size: 18),
                        Text(' ${q.rewardGems}', style: const TextStyle(color: Tokens.blueText, fontWeight: FontWeight.w800)),
                      ],
                    ]),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: q.target <= 0 ? 0 : (q.progress / q.target).clamp(0.0, 1.0),
                        minHeight: 14,
                        backgroundColor: Tokens.border,
                        color: q.completed ? Tokens.green : Tokens.gold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text('${q.progress} / ${q.target}', style: const TextStyle(color: Tokens.textMuted)),
                  ]),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
