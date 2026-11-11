import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/mascot.dart';
import '../learn/learn_providers.dart';
import 'mock_providers.dart';

/// Result of a submitted attempt: score, per-subject scores, lyceum comparison, prediction.
class MockResultScreen extends ConsumerWidget {
  const MockResultScreen({super.key, required this.attemptId, this.result});
  final String attemptId;
  final AttemptResult? result;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final r = result;
    if (r != null) return _Body(result: r);
    return Scaffold(
      body: AsyncView<AttemptResult>(
        value: ref.watch(attemptResultProvider(attemptId)),
        onRetry: () => ref.invalidate(attemptResultProvider(attemptId)),
        builder: (d) => _Body(result: d),
      ),
    );
  }
}

String _resp(Json? j) {
  if (j == null || j.isEmpty) return '—';
  return j.values.map((v) => v is List ? v.join(', ') : '$v').join('; ');
}

class _ReviewTile extends StatelessWidget {
  const _ReviewTile({required this.index, required this.row});
  final int index;
  final ReviewRow row;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final (icon, color, bg) = !row.answered
        ? (Icons.remove_circle_outline, Tokens.textMuted, Tokens.border)
        : row.correct
            ? (Icons.check_circle, Tokens.greenEdge, Tokens.greenSoft)
            : (Icons.cancel, Tokens.redEdge, Tokens.redSoft);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(Tokens.radius)),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: color),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${index + 1}. ${!row.answered ? l.notAnswered : row.correct ? l.correct : l.incorrect}',
                style: TextStyle(fontWeight: FontWeight.w800, color: color)),
            if (row.answered && !row.correct) Text('${l.yourAnswer}: ${_resp(row.response)}'),
            if (!row.correct) Text('${l.correctAnswer}: ${_resp(row.correctResponse)}'),
          ]),
        ),
      ]),
    );
  }
}

String _f(double v) => v.toStringAsFixed(v.truncateToDouble() == v ? 0 : 1);

class _Body extends ConsumerWidget {
  const _Body({required this.result});
  final AttemptResult result;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final tag = context.localeTag;
    final cmp = result.comparison;
    final prediction = ref.watch(predictionProvider).value;
    final subjects = {for (final s in ref.watch(subjectsProvider).value ?? const <Subject>[]) s.id: s};
    const muted = TextStyle(color: Tokens.textMuted, fontWeight: FontWeight.w800);
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                Center(child: Mascot(pose: (cmp?.onTrack ?? false) ? MascotPose.top : MascotPose.straight, size: 140)),
                Text(l.score, textAlign: TextAlign.center, style: muted),
                Text('${_f(result.total)} / ${_f(result.maxTotal)}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 40, fontWeight: FontWeight.w800, color: Tokens.green)),
                Text('${result.correct} / ${result.questions}', textAlign: TextAlign.center, style: muted),
                const SizedBox(height: 16),
                for (final e in result.subjectScores.entries)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(children: [
                      Expanded(
                        child: Text(
                          subjects[e.key] == null ? e.key : pickName(subjects[e.key]!.names, tag),
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                      ),
                      Text(_f(e.value), style: const TextStyle(fontWeight: FontWeight.w800)),
                    ]),
                  ),
                if (cmp != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: cmp.onTrack ? Tokens.greenSoft : Tokens.redSoft,
                      borderRadius: BorderRadius.circular(Tokens.radius),
                    ),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(cmp.onTrack ? l.onTrack : l.offTrack,
                          style: TextStyle(fontWeight: FontWeight.w800, color: cmp.onTrack ? Tokens.greenEdge : Tokens.redEdge)),
                      Text('${l.passingScore}: ${_f(cmp.passingScore)}${cmp.year != null ? ' (${cmp.year})' : ''}'),
                      Text('${l.gap}: ${cmp.gap > 0 ? '+' : ''}${_f(cmp.gap)}'),
                      if (cmp.competitionRatio != null) Text('${l.competition}: ${cmp.competitionRatio!.toStringAsFixed(1)}'),
                    ]),
                  ),
                ],
                if (result.review.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  Text(l.reviewAnswers, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  for (final (i, row) in result.review.indexed) _ReviewTile(index: i, row: row),
                ],
                if (prediction != null) ...[
                  const SizedBox(height: 16),
                  Text(l.predictedScore, textAlign: TextAlign.center, style: muted),
                  Text(_f(prediction.value),
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: Tokens.blue)),
                  Text('${_f(prediction.low)} – ${_f(prediction.high)}', textAlign: TextAlign.center, style: muted),
                ],
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              if (result.review.any((r) => !r.correct)) ...[
                ChunkyButton(label: l.drillWeakTopics, tone: ChunkyTone.blue, onPressed: () => context.go('/practice')),
                const SizedBox(height: 8),
              ],
              ChunkyButton(label: l.continueLabel, onPressed: () => context.go('/mocks')),
            ]),
          ),
        ]),
      ),
    );
  }
}
