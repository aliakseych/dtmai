import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../learn/learn_providers.dart';
import '../profile/profile_providers.dart';
import 'practice_providers.dart';

class PracticeScreen extends ConsumerWidget {
  const PracticeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final due = ref.watch(reviewDueProvider).value ?? 0;
    final weak = ref.watch(weakAreasProvider);
    final premium = ref.watch(billingProvider).value?.isPremium ?? false;
    final subjectId = ref.watch(currentSubjectIdProvider).value ?? 'current';

    Widget tile(IconData icon, Color color, String title, String? sub, VoidCallback onTap) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: InkWell(
            borderRadius: BorderRadius.circular(Tokens.radius),
            onTap: onTap,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
                borderRadius: BorderRadius.circular(Tokens.radius),
              ),
              child: Row(children: [
                Icon(icon, color: color, size: 32),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                    if (sub != null) Text(sub, style: const TextStyle(color: Tokens.textMuted)),
                  ]),
                ),
                const Icon(Icons.chevron_right_rounded, color: Tokens.textMuted),
              ]),
            ),
          ),
        );

    return Scaffold(
      appBar: AppBar(title: Text(l.practice)),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(reviewDueProvider);
          ref.invalidate(weakAreasProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            tile(Icons.replay_rounded, Tokens.red, l.mistakes, due > 0 ? '$due' : null,
                () => context.push('/session/review/$subjectId')),
            tile(Icons.library_books_rounded, Tokens.blue, l.bankDrill, null,
                () => context.push('/session/drill/$subjectId')),
            tile(Icons.auto_awesome_rounded, Tokens.gold, l.personalMock, premium ? null : l.premium,
                () => premium ? context.push('/mocks/run/personal') : context.push('/premium')),
            const SizedBox(height: 12),
            Text(l.weakTopics, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            AsyncView<List<WeakArea>>(
              value: weak,
              isEmpty: (d) => d.isEmpty,
              onRetry: () => ref.invalidate(weakAreasProvider),
              builder: (areas) => Column(children: [
                for (final a in areas)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: () => context.push(Uri(
                        path: '/session/drill/$subjectId',
                        queryParameters: {
                          if (a.topicId != null) 'topic': a.topicId!,
                          if (a.typeId != null) 'type': a.typeId!,
                        },
                      ).toString()),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(a.topicName ?? l.weakTopics, style: const TextStyle(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 4),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: LinearProgressIndicator(value: a.score.clamp(0.0, 1.0), minHeight: 12, backgroundColor: Tokens.border, color: Tokens.orange),
                        ),
                      ]),
                    ),
                  ),
              ]),
            ),
          ],
        ),
      ),
    );
  }
}
