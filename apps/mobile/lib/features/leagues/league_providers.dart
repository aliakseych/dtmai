import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';

/// Current weekly league (null when the user is not placed in one yet).
final leagueProvider = FutureProvider.autoDispose<League?>((ref) => ref.watch(apiProvider).league());

enum BoardKind { friends, lyceum }

/// Friends / target-lyceum leaderboard for a period (`week` or `all`).
final boardProvider = FutureProvider.autoDispose.family<Board, (BoardKind, String)>((ref, key) {
  final api = ref.watch(apiProvider);
  return key.$1 == BoardKind.friends ? api.friendsBoard(key.$2) : api.lyceumBoard(key.$2);
});
