import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api.dart';
import '../../core/api/api_client.dart';
import '../../core/api/token_storage.dart';
import '../../core/l10n_ext.dart';
import '../../core/models.dart';
import '../../theme/tokens.dart';
import '../../widgets/async_view.dart';
import '../../widgets/chunky_button.dart';
import '../../widgets/guest_gate.dart';
import '../auth/auth_providers.dart';
import '../auth/language_picker.dart';
import 'profile_providers.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    return Scaffold(
      appBar: AppBar(title: Text(l.profile), actions: const [LanguagePicker()]),
      body: GuestGate(child: _Body()),
    );
  }
}

class _Body extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final me = ref.watch(meProvider);
    final stats = ref.watch(statsProvider);
    final billing = ref.watch(billingProvider);
    final friends = ref.watch(friendsProvider);
    return AsyncView<Me?>(
      value: me,
      onRetry: () {
        ref.invalidate(meProvider);
        ref.invalidate(statsProvider);
      },
      builder: (m) => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(m?.name ?? '', style: Theme.of(context).textTheme.headlineSmall),
          if (m?.email != null) Text(m!.email!, style: const TextStyle(color: Tokens.textMuted)),
          if (m != null && m.email == null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Tokens.blueSoft, borderRadius: BorderRadius.circular(Tokens.radius)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(l.saveProgress, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                const SizedBox(height: 4),
                Text(l.saveProgressBody),
                const SizedBox(height: 12),
                ChunkyButton(label: l.signIn, tone: ChunkyTone.blue, onPressed: () => context.push('/login')),
              ]),
            ),
          ],
          const SizedBox(height: 16),
          stats.maybeWhen(
            data: (s) => s == null ? const SizedBox.shrink() : Column(children: [_statGrid(context, s), _StreakCard(stats: s)]),
            orElse: () => const SizedBox.shrink(),
          ),
          const SizedBox(height: 16),
          billing.maybeWhen(
            data: (b) => b == null ? const SizedBox.shrink() : _PlanTile(billing: b),
            orElse: () => const SizedBox.shrink(),
          ),
          _NavTile(icon: Icons.assignment_turned_in_outlined, label: l.quests, onTap: () => context.push('/quests')),
          _NavTile(icon: Icons.school_outlined, label: l.lyceums, onTap: () => context.push('/lyceums')),
          _NavTile(icon: Icons.emoji_events_outlined, label: l.leagues, onTap: () => context.go('/leagues')),
          _NavTile(icon: Icons.notifications_outlined, label: l.notificationSettings, onTap: () => context.push('/settings/notifications')),
          const SizedBox(height: 16),
          Text(l.friends, style: Theme.of(context).textTheme.titleMedium),
          friends.when(
            loading: () => const Padding(padding: EdgeInsets.all(16), child: LinearProgressIndicator()),
            error: (_, __) => TextButton(onPressed: () => ref.invalidate(friendsProvider), child: Text(l.retry)),
            data: (list) => list.isEmpty
                ? Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Text(l.noFriends))
                : Column(
                    children: [
                      for (final f in list)
                        ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(f.name),
                          trailing: Text('${f.xp} ${l.xp}', style: const TextStyle(fontWeight: FontWeight.w700)),
                        ),
                    ],
                  ),
          ),
          const SizedBox(height: 24),
          ChunkyButton(
            label: l.logout,
            tone: ChunkyTone.white,
            onPressed: () async {
              // A guest has no credentials to come back with: warn before dropping the progress.
              if (m != null && m.email == null) {
                final ok = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: Text(l.guestLogoutTitle),
                    content: Text(l.guestLogoutBody),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(ctx, false), child: Text(l.cancel)),
                      TextButton(onPressed: () => Navigator.pop(ctx, true), child: Text(l.logout)),
                    ],
                  ),
                );
                if (ok != true) return;
              }
              final storage = ref.read(tokenStorageProvider);
              final pair = await storage.read();
              if (pair != null) {
                try {
                  await ref.read(apiProvider).logout(pair.refresh);
                } catch (_) {
                  // Local sign-out must succeed even when offline.
                }
              }
              await ref.read(authProvider.notifier).signOut();
            },
          ),
        ],
      ),
    );
  }

  Widget _statGrid(BuildContext context, Stats s) {
    final l = context.l10n;
    Widget cell(String label, String value, Color c) => Expanded(
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
              borderRadius: BorderRadius.circular(Tokens.radius),
            ),
            child: Column(
              children: [
                Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: c)),
                Text(label, style: const TextStyle(color: Tokens.textMuted, fontSize: 12)),
              ],
            ),
          ),
        );
    return Row(
      children: [
        cell(l.xp, '${s.xpTotal}', Tokens.blueText),
        const SizedBox(width: 8),
        cell(l.gems, '${s.gems}', Tokens.blueText),
        const SizedBox(width: 8),
        cell(l.hearts, s.hearts.unlimited ? '∞' : '${s.hearts.count}', Tokens.red),
        const SizedBox(width: 8),
        cell(l.streakLabel, '${s.streak}', Tokens.goldText),
      ],
    );
  }
}

class _NavTile extends StatelessWidget {
  const _NavTile({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
        contentPadding: EdgeInsets.zero,
        leading: Icon(icon, color: Tokens.blueText),
        title: Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      );
}

/// Read-only entitlement row; opens the status screen (no purchase flow on mobile).
class _PlanTile extends StatelessWidget {
  const _PlanTile({required this.billing});
  final Billing billing;

  @override
  Widget build(BuildContext context) {
    final l = context.l10n;
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(Icons.workspace_premium, color: billing.isPremium ? Tokens.goldText : Tokens.textMuted),
      title: Text(l.premium, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text(billing.isPremium ? l.planPremium : l.planFree),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => context.push('/premium'),
    );
  }
}

/// Streak freezes (use one), at-risk hint and the daily XP goal picker.
class _StreakCard extends ConsumerWidget {
  const _StreakCard({required this.stats});
  final Stats stats;

  static const _goals = [10, 20, 30, 50, 100];

  void _toast(BuildContext c, String m) => ScaffoldMessenger.of(c).showSnackBar(SnackBar(content: Text(m)));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l10n;
    final goals = {..._goals, stats.dailyGoalXp}.toList()..sort();
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: Tokens.border, width: Tokens.borderWidth),
        borderRadius: BorderRadius.circular(Tokens.radius),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        if (stats.streakAtRisk)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(l.streakAtRisk, style: const TextStyle(color: Tokens.orange, fontWeight: FontWeight.w800)),
          ),
        Row(children: [
          const Icon(Icons.ac_unit_rounded, color: Tokens.blue),
          const SizedBox(width: 8),
          Expanded(child: Text(l.streakFreezes(stats.streakFreezes), style: const TextStyle(fontWeight: FontWeight.w700))),
          ChunkyButton(
            label: l.useFreeze,
            expand: false,
            tone: ChunkyTone.blue,
            onPressed: stats.streakFreezes > 0
                ? () async {
                    try {
                      await ref.read(apiProvider).useStreakFreeze();
                      ref.invalidate(statsProvider);
                      if (context.mounted) _toast(context, l.freezeUsed);
                    } catch (e) {
                      if (context.mounted) _toast(context, apiErrorMessage(e, l.errorGeneric));
                    }
                  }
                : null,
          ),
        ]),
        const SizedBox(height: 16),
        Text(l.dailyGoal, style: const TextStyle(fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        Wrap(spacing: 8, children: [
          for (final g in goals)
            ChoiceChip(
              label: Text('$g ${l.xp}'),
              selected: g == stats.dailyGoalXp,
              onSelected: (_) async {
                try {
                  await ref.read(apiProvider).setDailyGoal(g);
                  ref.invalidate(statsProvider);
                } catch (e) {
                  if (context.mounted) _toast(context, apiErrorMessage(e, l.errorGeneric));
                }
              },
            ),
        ]),
      ]),
    );
  }
}
