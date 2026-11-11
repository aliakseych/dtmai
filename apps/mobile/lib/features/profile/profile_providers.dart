import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';
import '../auth/auth_providers.dart';

bool _signedIn(Ref ref) => ref.watch(authProvider) == AuthStatus.signedIn;

/// Current user; null for guests.
final meProvider = FutureProvider<Me?>((ref) async {
  if (!_signedIn(ref)) return null;
  return ref.watch(apiProvider).me();
});

/// Hearts, streak, XP, gems; null for guests.
final statsProvider = FutureProvider<Stats?>((ref) async {
  if (!_signedIn(ref)) return null;
  return ref.watch(apiProvider).stats();
});

/// Entitlement status (read only); null for guests.
final billingProvider = FutureProvider<Billing?>((ref) async {
  if (!_signedIn(ref)) return null;
  return ref.watch(apiProvider).billing();
});

final friendsProvider = FutureProvider<List<Friend>>((ref) async {
  if (!_signedIn(ref)) return const [];
  return ref.watch(apiProvider).friends();
});
