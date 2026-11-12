import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/mascot.dart';
import '../profile/profile_providers.dart';
import 'premium_providers.dart';

/// Read-only plan status. Payments are disabled, so no prices or purchase actions are shown.
class PremiumScreen extends ConsumerWidget {
  const PremiumScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final tag = context.localeTag;
    final billing = ref.watch(billingProvider).value;
    final plans = ref.watch(plansProvider);
    final until = billing?.until;

    return Scaffold(
      appBar: AppBar(title: Text(l.premium)),
      body: AsyncView<List<Plan>>(
        value: plans,
        onRetry: () => ref.invalidate(plansProvider),
        builder: (list) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Center(child: Mascot(pose: MascotPose.premium, size: 120)),
            const SizedBox(height: 8),
            Text(
              billing?.isPremium == true && until != null
                  ? l.planActive(DateFormat.yMMMd(tag).format(until))
                  : l.planFree,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 16),
            Text(l.premiumPerks, style: const TextStyle(color: Tokens.textMuted, fontWeight: FontWeight.w700)),
            const SizedBox(height: 16),
            for (final p in list)
              Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  border: Border.all(color: p.code == billing?.planCode ? Tokens.gold : Tokens.border, width: Tokens.borderWidth),
                  borderRadius: BorderRadius.circular(Tokens.radius),
                ),
                child: Row(children: [
                  Expanded(
                    child: Text(pickName(p.names, tag), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                  ),
                ]),
              ),
          ],
        ),
      ),
    );
  }
}
