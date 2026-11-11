import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import 'mock_providers.dart';

/// Previous-year official papers (timed practice papers). Mocks are free.
class MocksScreen extends ConsumerWidget {
  const MocksScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final tag = context.localeTag;
    final mocks = ref.watch(mocksProvider);
    final active = ref.watch(activeAttemptProvider).value;
    final prediction = ref.watch(predictionProvider).value;
    final history = ref.watch(historyProvider).value ?? const <HistoryItem>[];

    Future<void> refresh() async {
      ref.invalidate(mocksProvider);
      ref.invalidate(activeAttemptProvider);
      ref.invalidate(predictionProvider);
      ref.invalidate(historyProvider);
    }

    return Scaffold(
      appBar: AppBar(title: Text(l.mocks)),
      body: AsyncView<List<Mock>>(
        value: mocks,
        isEmpty: (d) => d.isEmpty && active == null,
        onRetry: refresh,
        builder: (list) => RefreshIndicator(
          onRefresh: refresh,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (active != null && active.status == 'in_progress')
                _Card(
                  color: Tokens.blueSoft,
                  child: Row(children: [
                    Expanded(
                      child: Text(l.resumeAttempt, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                    ),
                    ChunkyButton(
                      label: l.continueLabel,
                      expand: false,
                      tone: ChunkyTone.blue,
                      onPressed: () => context.push('/mocks/run/$resumeMockId'),
                    ),
                  ]),
                ),
              if (prediction != null)
                _Card(
                  color: Tokens.greenSoft,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(l.predictedScore, style: const TextStyle(color: Tokens.textMuted, fontWeight: FontWeight.w700)),
                    Text(
                      prediction.value.toStringAsFixed(1),
                      style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Tokens.greenEdge),
                    ),
                    Text('${prediction.low.toStringAsFixed(1)} – ${prediction.high.toStringAsFixed(1)}',
                        style: const TextStyle(color: Tokens.textMuted)),
                  ]),
                ),
              for (final m in list)
                _Card(
                  child: Row(children: [
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(pickName(m.names, tag), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                        Text('${m.questionCount} · ${l.minutesShort(m.durationMin)}', style: const TextStyle(color: Tokens.textMuted)),
                      ]),
                    ),
                    ChunkyButton(label: l.start, expand: false, tone: ChunkyTone.blue, onPressed: () => context.push('/mocks/run/${m.id}')),
                  ]),
                ),
              if (history.isNotEmpty) ...[
                Padding(
                  padding: const EdgeInsets.only(top: 8, bottom: 8),
                  child: Text(l.history, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                ),
                for (final h in history)
                  InkWell(
                    borderRadius: BorderRadius.circular(Tokens.radius),
                    onTap: () => context.push('/mocks/result/${h.attemptId}'),
                    child: _Card(
                      child: Row(children: [
                        Expanded(
                          child: Text(
                            h.submittedAt == null ? h.kind : DateFormat.yMMMd(tag).add_Hm().format(h.submittedAt!),
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                        ),
                        Text('${h.score.toStringAsFixed(h.score.truncateToDouble() == h.score ? 0 : 1)} / ${h.maxTotal.toStringAsFixed(0)}',
                            style: const TextStyle(fontWeight: FontWeight.w800, color: Tokens.greenText)),
                      ]),
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

class _Card extends StatelessWidget {
  const _Card({required this.child, this.color});
  final Widget child;
  final Color? color;

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: color,
          border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
          borderRadius: BorderRadius.circular(Tokens.radius),
        ),
        child: child,
      );
}
