import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/mascot.dart';
import '../learn/learn_providers.dart';
import '../profile/profile_providers.dart';

/// Celebration after a finished session: XP, accuracy and current streak.
class DoneScreen extends ConsumerWidget {
  const DoneScreen({super.key, required this.result});
  final FinishResult result;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final stats = ref.watch(statsProvider).value;
    final perfect = result.total > 0 && result.correct == result.total;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              Expanded(
                child: Center(
                  child: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Mascot(pose: perfect ? MascotPose.trophy : MascotPose.celebrate, size: 180),
                        const SizedBox(height: 16),
                        Text(
                          l.lessonComplete,
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Tokens.goldText),
                        ),
                        if (result.mode == 'placement') ...[
                          const SizedBox(height: 8),
                          Text(l.placementDone, textAlign: TextAlign.center),
                        ],
                        const SizedBox(height: 24),
                        Wrap(
                          alignment: WrapAlignment.center,
                          spacing: 12,
                          runSpacing: 12,
                          children: [
                            _Stat(color: Tokens.gold, label: l.xp, value: '+${result.xpBase}'),
                            _Stat(color: Tokens.green, label: l.accuracy, value: '${result.correct}/${result.total}'),
                            if (stats != null)
                              _Stat(color: Tokens.orange, label: l.streakLabel, value: l.streakDays(stats.streak)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              ChunkyButton(
                label: l.continueLabel,
                onPressed: () {
                  ref.invalidate(pathProvider);
                  ref.invalidate(statsProvider);
                  context.go('/learn');
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.color, required this.label, required this.value});
  final Color color;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 104,
      decoration: BoxDecoration(border: Border.all(color: color, width: 2), borderRadius: BorderRadius.circular(Tokens.radius)),
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 4),
            decoration: BoxDecoration(color: color, borderRadius: const BorderRadius.vertical(top: Radius.circular(Tokens.radius - 2))),
            child: Text(
              label.toUpperCase(),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 11),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
            child: Text(value, textAlign: TextAlign.center, style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 18)),
          ),
        ],
      ),
    );
  }
}
