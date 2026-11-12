import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/l10n_ext.dart';
import '../features/auth/auth_providers.dart';
import '../features/profile/profile_providers.dart';
import 'async_view.dart';
import 'chunky_button.dart';
import 'mascot.dart';

/// Shows [child] for signed-in users, otherwise a friendly sign-in prompt.
class GuestGate extends ConsumerWidget {
  const GuestGate({super.key, required this.child, this.requireAccount = false});
  final Widget child;

  /// When true, anonymous guests (no email) are prompted to sign in too.
  final bool requireAccount;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(authProvider);
    if (status == AuthStatus.signedIn && !requireAccount) return child;
    if (status == AuthStatus.signedIn) {
      final me = ref.watch(meProvider);
      if (me.isLoading) return const Center(child: CircularProgressIndicator());
      if (me.value?.email != null || me.hasError) return child;
    }
    if (status == AuthStatus.unknown) return const Center(child: CircularProgressIndicator());
    final l = context.l10n;
    return MascotMessage(
      pose: MascotPose.wave,
      message: l.guestGateMessage,
      action: ChunkyButton(label: l.signIn, expand: false, onPressed: () => context.push('/login')),
    );
  }
}
