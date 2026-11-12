import 'dart:async';

import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/mascot.dart';
import '../../widgets/math_text.dart';
import '../practice/practice_providers.dart';
import '../profile/profile_providers.dart';
import 'question_view.dart';
import 'session_providers.dart';

/// Lesson player: answer -> CHECK -> feedback sheet -> CONTINUE. Used by lessons,
/// placement, mistakes review and bank/weak-area drills (`mode`).
class LessonScreen extends ConsumerWidget {
  const LessonScreen({super.key, required this.mode, this.refId, this.topicId, this.typeId});
  final String mode;
  final String? refId;
  final String? topicId;
  final String? typeId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final args = (mode: mode, refId: refId, topicId: topicId, typeId: typeId);
    final session = ref.watch(sessionProvider(args));
    return Scaffold(
      body: SafeArea(
        child: session.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => isNoHearts(e)
              ? OutOfHearts(allowReview: mode != 'review', onBack: () => context.go('/learn'))
              : Column(
                  children: [
                    Align(alignment: Alignment.centerLeft, child: CloseButton(onPressed: () => context.go('/learn'))),
                    Expanded(
                      child: MascotMessage(
                        pose: MascotPose.sad,
                        message: apiErrorMessage(e, context.l10n.errorGeneric),
                        action: ChunkyButton(
                          label: context.l10n.retry,
                          expand: false,
                          tone: ChunkyTone.blue,
                          onPressed: () => ref.invalidate(sessionProvider(args)),
                        ),
                      ),
                    ),
                  ],
                ),
          data: (s) => s.items.isEmpty
              ? Column(
                  children: [
                    Align(alignment: Alignment.centerLeft, child: CloseButton(onPressed: () => context.go('/learn'))),
                    Expanded(child: MascotMessage(pose: MascotPose.sleep, message: context.l10n.empty)),
                  ],
                )
              : _Player(session: s),
        ),
      ),
    );
  }
}

/// Shown when the learner has no hearts: earn hearts through a review, or wait for the refill.
class OutOfHearts extends ConsumerWidget {
  const OutOfHearts({super.key, required this.allowReview, required this.onBack});
  final bool allowReview;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final refill = ref.watch(statsProvider).value?.hearts.nextRefillAt;
    final due = allowReview ? ref.watch(reviewDueProvider).value : null;
    return Column(
      children: [
        Align(alignment: Alignment.centerLeft, child: CloseButton(onPressed: onBack)),
        Expanded(
          child: MascotMessage(
            pose: MascotPose.sad,
            message: l.noHearts,
            action: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (allowReview && (due == null || due > 0))
                  ChunkyButton(
                    label: l.reviewToEarn,
                    tone: ChunkyTone.green,
                    onPressed: () => context.pushReplacement('/session/review/current'),
                  ),
                if (allowReview && due == 0)
                  Text(l.noReviewDue, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700, color: Tokens.textMuted)),
                if (refill != null) ...[
                  const SizedBox(height: 16),
                  _RefillTimer(until: refill),
                ],
                const SizedBox(height: 16),
                ChunkyButton(label: l.waitForRefill, tone: ChunkyTone.white, onPressed: onBack),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _RefillTimer extends StatelessWidget {
  const _RefillTimer({required this.until});
  final DateTime until;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<int>(
      stream: Stream.periodic(const Duration(seconds: 1), (i) => i),
      builder: (_, _) {
        final left = until.difference(DateTime.now());
        final d = left.isNegative ? Duration.zero : left;
        final h = d.inHours;
        final m = (d.inMinutes % 60).toString().padLeft(2, '0');
        final s = (d.inSeconds % 60).toString().padLeft(2, '0');
        return Text(
          context.l10n.refillIn(h > 0 ? '$h:$m:$s' : '$m:$s'),
          style: const TextStyle(fontWeight: FontWeight.w800, color: Tokens.textMuted),
        );
      },
    );
  }
}

class _Player extends ConsumerStatefulWidget {
  const _Player({required this.session});
  final SessionData session;

  @override
  ConsumerState<_Player> createState() => _PlayerState();
}

class _PlayerState extends ConsumerState<_Player> {
  late final List<Item> _items = [...widget.session.items];
  int _index = 0;
  Json? _answer;
  AnswerResult? _result;
  late int? _hearts = widget.session.hearts;
  late bool _unlimited = widget.session.unlimitedHearts;
  late int _answered = widget.session.answered;
  late int _total = widget.session.total;
  bool _busy = false;
  bool _blocked = false;
  final _clock = Stopwatch()..start();

  Item get _item => _items[_index];
  bool get _noHeartsLeft => !_unlimited && _hearts != null && _hearts! <= 0;

  Future<void> _check() async {
    if (_busy || !isAnswered(_item, _answer)) return;
    setState(() => _busy = true);
    try {
      final r = await ref.read(apiProvider).answer(widget.session.id, _item.id, _answer!, _clock.elapsedMilliseconds);
      if (!mounted) return;
      setState(() {
        _result = r;
        _hearts = r.hearts ?? _hearts;
        _unlimited = r.unlimitedHearts;
        _answered = r.answered;
        _total = r.total;
        _busy = false;
        final next = r.nextItem;
        if (next != null && !_items.any((i) => i.id == next.id)) _items.add(next);
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _busy = false;
        _blocked = isNoHearts(e);
      });
      if (!_blocked) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
      }
    }
  }

  Future<void> _next() async {
    final r = _result;
    if (r == null) return;
    if (r.sessionDone || _index + 1 >= _items.length) {
      await _finish();
      return;
    }
    setState(() {
      _index++;
      _answer = null;
      _result = null;
      _clock
        ..reset()
        ..start();
    });
  }

  Future<void> _finish() async {
    setState(() => _busy = true);
    try {
      final res = await ref.read(apiProvider).finishSession(widget.session.id);
      ref.invalidate(statsProvider);
      if (!mounted) return;
      context.go('/done', extra: res);
    } catch (e) {
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
    }
  }

  Future<void> _confirmExit() async {
    final l = context.l10n;
    final leave = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l.exitConfirmTitle),
        content: Text(l.exitConfirmBody),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(l.cancel)),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: Text(l.leave)),
        ],
      ),
    );
    if (leave == true) await _exit();
  }

  /// Closes the session server-side (keeps earned XP) and returns to the path.
  Future<void> _exit() async {
    try {
      await ref.read(apiProvider).finishSession(widget.session.id);
      ref.invalidate(statsProvider);
    } catch (_) {}
    if (mounted) context.go('/learn');
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    if (_blocked) {
      return OutOfHearts(allowReview: widget.session.mode != 'review', onBack: _exit);
    }
    final r = _result;
    final progress = _total == 0 ? 0.0 : (_answered / _total).clamp(0.0, 1.0);
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _confirmExit();
      },
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(4, 8, 16, 0),
            child: Row(
              children: [
                IconButton(icon: const Icon(Icons.close_rounded), onPressed: _confirmExit),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 16,
                      color: Tokens.green,
                      backgroundColor: Tokens.border,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.favorite_rounded, color: Tokens.red),
                const SizedBox(width: 4),
                Text(
                  _unlimited ? '∞' : '${_hearts ?? ''}',
                  style: const TextStyle(color: Tokens.red, fontWeight: FontWeight.w800, fontSize: 16),
                ),
              ],
            ),
          ),
          if (_noHeartsLeft)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(color: Tokens.redSoft, borderRadius: BorderRadius.circular(12)),
              child: Row(
                children: [
                  const Icon(Icons.heart_broken_rounded, color: Tokens.red),
                  const SizedBox(width: 8),
                  Expanded(child: Text(l.heartsBanner, style: const TextStyle(fontWeight: FontWeight.w700))),
                ],
              ),
            ),
          Expanded(
            child: QuestionView(
              key: ValueKey(_item.id),
              item: _item,
              answer: _answer,
              locked: r != null,
              correctResponse: r?.correctResponse,
              onChanged: (a) => setState(() => _answer = a),
            ),
          ),
          if (r == null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: ChunkyButton(
                label: l.check,
                loading: _busy,
                onPressed: isAnswered(_item, _answer) ? _check : null,
              ),
            )
          else
            _FeedbackSheet(item: _item, result: r, busy: _busy, onContinue: _next),
        ],
      ),
    );
  }
}

class _FeedbackSheet extends ConsumerStatefulWidget {
  const _FeedbackSheet({required this.item, required this.result, required this.busy, required this.onContinue});
  final Item item;
  final AnswerResult result;
  final bool busy;
  final VoidCallback onContinue;

  @override
  ConsumerState<_FeedbackSheet> createState() => _FeedbackSheetState();
}

class _FeedbackSheetState extends ConsumerState<_FeedbackSheet> {
  String? _explanation;
  bool _explaining = false;
  bool _reported = false;

  Item get item => widget.item;
  AnswerResult get result => widget.result;

  void _toast(String m) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

  Future<void> _explain() async {
    setState(() => _explaining = true);
    try {
      final text = await ref.read(apiProvider).explain(item.id, context.localeTag);
      if (mounted) setState(() => _explanation = text);
    } catch (e) {
      // Premium / quota errors carry a readable `detail`.
      if (mounted) _toast(apiErrorMessage(e, context.l10n.errorGeneric));
    } finally {
      if (mounted) setState(() => _explaining = false);
    }
  }

  Future<void> _report() async {
    final l = context.l10n;
    final ctrl = TextEditingController();
    final reason = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l.reportQuestion),
        content: TextField(
          controller: ctrl,
          maxLength: 500,
          maxLines: 3,
          decoration: InputDecoration(hintText: l.reportReason),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l.cancel)),
          TextButton(onPressed: () => Navigator.pop(ctx, ctrl.text.trim()), child: Text(l.send)),
        ],
      ),
    );
    ctrl.dispose();
    if (reason == null || reason.isEmpty || !mounted) return;
    try {
      await ref.read(apiProvider).reportQuestion(item.id, reason);
      if (!mounted) return;
      setState(() => _reported = true);
      _toast(l.reportSent);
    } catch (e) {
      if (mounted) _toast(apiErrorMessage(e, l.errorGeneric));
    }
  }

  @override
  Widget build(BuildContext context) {
    final busy = widget.busy;
    final onContinue = widget.onContinue;
    final l = context.l10n;
    final ok = result.correct;
    final color = ok ? Tokens.greenEdge : Tokens.redEdge;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      color: ok ? Tokens.greenSoft : Tokens.redSoft,
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(ok ? Icons.check_circle_rounded : Icons.cancel_rounded, color: color, size: 32),
                const SizedBox(width: 8),
                Text(ok ? l.correct : l.incorrect, style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 20)),
              ],
            ),
            if (!ok) ...[
              const SizedBox(height: 8),
              Text(l.correctAnswer, style: TextStyle(color: color, fontWeight: FontWeight.w800)),
              MathText(formatCorrect(item, result.correctResponse), style: TextStyle(color: color)),
            ],
            if (_explanation != null) ...[
              const SizedBox(height: 8),
              MathText(_explanation!, style: const TextStyle(color: Tokens.text, fontSize: 15)),
            ],
            const SizedBox(height: 4),
            Row(children: [
              if (_explanation == null)
                TextButton.icon(
                  onPressed: _explaining ? null : _explain,
                  icon: _explaining
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.lightbulb_outline_rounded),
                  label: Text(l.explain),
                ),
              const Spacer(),
              TextButton.icon(
                onPressed: _reported ? null : _report,
                icon: const Icon(Icons.flag_outlined),
                label: Text(l.reportQuestion),
              ),
            ]),
            const SizedBox(height: 4),
            ChunkyButton(
              label: l.continueLabel,
              tone: ok ? ChunkyTone.green : ChunkyTone.red,
              loading: busy,
              onPressed: onContinue,
            ),
          ],
        ),
      ),
    );
  }
}
