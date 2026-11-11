import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../lesson/question_view.dart';
import 'mock_providers.dart';

/// Timed practice-paper runner: countdown, navigator, mark-for-review, autosave.
/// [blueprintId] is a blueprint id, [personalMockId] or [resumeMockId].
class MockRunnerScreen extends ConsumerWidget {
  const MockRunnerScreen({super.key, required this.blueprintId});
  final String blueprintId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: AsyncView<Attempt>(
        value: ref.watch(attemptProvider(blueprintId)),
        onRetry: () => ref.invalidate(attemptProvider(blueprintId)),
        builder: (a) => _Runner(attempt: a),
      ),
    );
  }
}

class _Runner extends ConsumerStatefulWidget {
  const _Runner({required this.attempt});
  final Attempt attempt;

  @override
  ConsumerState<_Runner> createState() => _RunnerState();
}

class _RunnerState extends ConsumerState<_Runner> with WidgetsBindingObserver {
  int _index = 0;
  late final Json _answers = Map<String, dynamic>.from(widget.attempt.answers);
  late final Set<String> _flags = {...widget.attempt.flags};
  // The countdown derives from the server deadline: `_deadline - (now + _skew)`, where `_skew`
  // is the server clock minus the device clock. It survives backgrounding and clock changes.
  late DateTime _deadline;
  Duration _skew = Duration.zero;
  late int _left;
  Timer? _ticker;
  Timer? _debounce;
  bool _submitting = false;
  bool _saveFailed = false;
  bool _rejected = false;

  Item get _item => widget.attempt.items[_index];

  void _syncClock(Attempt a) {
    final now = DateTime.now();
    if (a.deadline != null && a.serverNow != null) {
      _deadline = a.deadline!;
      _skew = a.serverNow!.difference(now);
    } else {
      _deadline = now.add(Duration(seconds: a.timeLeftS));
      _skew = Duration.zero;
    }
  }

  int _remaining() {
    final ms = _deadline.difference(DateTime.now().add(_skew)).inMilliseconds;
    return ms <= 0 ? 0 : (ms / 1000).ceil();
  }

  void _tick() {
    if (!mounted || _submitting) return;
    final left = _remaining();
    setState(() => _left = left);
    if (left <= 0) _submit();
  }

  @override
  void initState() {
    super.initState();
    _syncClock(widget.attempt);
    _left = _remaining();
    WidgetsBinding.instance.addObserver(this);
    _ticker = Timer.periodic(const Duration(seconds: 1), (_) => _tick());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _tick();
    } else if (!_submitting) {
      // Flush pending answers before the OS may suspend or kill the app.
      _debounce?.cancel();
      _save();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _ticker?.cancel();
    _debounce?.cancel();
    super.dispose();
  }

  void _changed() {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 600), _save);
  }

  Future<void> _save() async {
    try {
      final saved = await ref.read(apiProvider).saveAttempt(widget.attempt.id, _answers, _flags.toList());
      if (!mounted) return;
      _syncClock(saved);
      if (!saved.accepted) {
        // Deadline passed: the server ignored these answers. Grade what it already has.
        setState(() => _rejected = true);
        _submit();
      } else if (_saveFailed) {
        setState(() => _saveFailed = false);
      }
    } catch (_) {
      if (mounted) setState(() => _saveFailed = true);
    }
  }

  Future<void> _submit() async {
    if (_submitting) return;
    setState(() => _submitting = true);
    _debounce?.cancel();
    try {
      final api = ref.read(apiProvider);
      // Persist the latest state first so the server grades what is on screen.
      // A failed save must not block submitting (e.g. the deadline already passed).
      try {
        await api.saveAttempt(widget.attempt.id, _answers, _flags.toList());
      } catch (_) {}
      final result = await api.submitAttempt(widget.attempt.id);
      ref.invalidate(activeAttemptProvider);
      ref.invalidate(predictionProvider);
      if (mounted) context.pushReplacement('/mocks/result/${widget.attempt.id}', extra: result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(apiErrorMessage(e, context.l10n.errorGeneric))));
    }
  }

  Future<void> _confirmSubmit() async {
    final l = context.l10n;
    final items = widget.attempt.items;
    final unanswered = items.where((i) => !isAnswered(i, _answers[i.id] as Json?)).length;
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.submitConfirmTitle),
        content: Text(l.submitConfirmBody(unanswered, _flags.length)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)),
          TextButton(onPressed: () => Navigator.pop(c, true), child: Text(l.submit)),
        ],
      ),
    );
    if (ok == true) _submit();
  }

  Future<void> _confirmExit() async {
    final l = context.l10n;
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.exitMockTitle),
        content: Text(l.exitMockBody),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)),
          TextButton(onPressed: () => Navigator.pop(c, true), child: Text(l.leave)),
        ],
      ),
    );
    if (ok == true) {
      await _save();
      if (mounted) context.go('/mocks');
    }
  }

  String _fmt(int s) {
    final m = (s ~/ 60).toString().padLeft(2, '0');
    final r = (s % 60).toString().padLeft(2, '0');
    return '$m:$r';
  }

  void _openNavigator() {
    final l = context.l10n;
    showModalBottomSheet<void>(
      context: context,
      builder: (c) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(l.navigator, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            const SizedBox(height: 12),
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (var i = 0; i < widget.attempt.items.length; i++)
                _NavCell(
                  number: i + 1,
                  current: i == _index,
                  answered: isAnswered(widget.attempt.items[i], _answers[widget.attempt.items[i].id] as Json?),
                  flagged: _flags.contains(widget.attempt.items[i].id),
                  onTap: () {
                    Navigator.pop(c);
                    setState(() => _index = i);
                  },
                ),
            ]),
          ]),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    final items = widget.attempt.items;
    final item = _item;
    final flagged = _flags.contains(item.id);
    final answered = items.where((i) => isAnswered(i, _answers[i.id] as Json?)).length;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _confirmExit();
      },
      child: SafeArea(
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 8, 8, 0),
            child: Row(children: [
              IconButton(icon: const Icon(Icons.close_rounded), onPressed: _confirmExit),
              Expanded(
                child: Text('${_index + 1} / ${items.length}  ·  ${l.answeredCount(answered, items.length)}',
                    style: const TextStyle(fontWeight: FontWeight.w700, color: Tokens.textMuted)),
              ),
              Icon(Icons.timer_outlined, color: _left < 60 ? Tokens.red : Tokens.textMuted),
              const SizedBox(width: 4),
              Text(_fmt(_left),
                  style: TextStyle(fontWeight: FontWeight.w800, color: _left < 60 ? Tokens.red : Tokens.text)),
              IconButton(icon: const Icon(Icons.grid_view_rounded), tooltip: l.navigator, onPressed: _openNavigator),
            ]),
          ),
          if (_rejected)
            MaterialBanner(
              content: Text(l.answersNotAccepted),
              backgroundColor: Tokens.redSoft,
              actions: const [SizedBox.shrink()],
            ),
          if (_saveFailed)
            MaterialBanner(
              content: Text(l.autosaveFailed),
              backgroundColor: Tokens.redSoft,
              actions: [TextButton(onPressed: _save, child: Text(l.retry))],
            ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                QuestionView(
                  key: ValueKey(item.id),
                  item: item,
                  answer: _answers[item.id] as Json?,
                  locked: _submitting,
                  onChanged: (a) {
                    setState(() {
                      if (a == null) {
                        _answers.remove(item.id);
                      } else {
                        _answers[item.id] = a;
                      }
                    });
                    _changed();
                  },
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              IconButton(
                tooltip: l.markReview,
                icon: Icon(flagged ? Icons.flag_rounded : Icons.outlined_flag_rounded, color: flagged ? Tokens.orange : Tokens.textMuted),
                onPressed: () {
                  setState(() => flagged ? _flags.remove(item.id) : _flags.add(item.id));
                  _changed();
                },
              ),
              const SizedBox(width: 4),
              if (_index > 0)
                IconButton(icon: const Icon(Icons.chevron_left_rounded), onPressed: () => setState(() => _index--)),
              const Spacer(),
              if (_index < items.length - 1)
                ChunkyButton(
                  label: l.continueLabel,
                  expand: false,
                  tone: ChunkyTone.blue,
                  onPressed: () => setState(() => _index++),
                )
              else
                ChunkyButton(label: l.submit, expand: false, loading: _submitting, onPressed: _confirmSubmit),
            ]),
          ),
          if (_index < items.length - 1)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: TextButton(onPressed: _submitting ? null : _confirmSubmit, child: Text(l.submit)),
            ),
        ]),
      ),
    );
  }
}

class _NavCell extends StatelessWidget {
  const _NavCell({required this.number, required this.current, required this.answered, required this.flagged, required this.onTap});
  final int number;
  final bool current;
  final bool answered;
  final bool flagged;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        width: 44,
        height: 44,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: answered ? Tokens.blueSoft : Colors.white,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: current ? Tokens.blue : Tokens.border, width: current ? 3 : 2),
        ),
        child: Stack(alignment: Alignment.center, children: [
          Text('$number', style: const TextStyle(fontWeight: FontWeight.w800)),
          if (flagged) const Positioned(top: 2, right: 2, child: Icon(Icons.flag_rounded, size: 12, color: Tokens.orange)),
        ]),
      ),
    );
  }
}
