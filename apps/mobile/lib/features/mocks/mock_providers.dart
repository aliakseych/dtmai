import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';
import '../auth/auth_providers.dart';
import '../learn/learn_providers.dart';

/// Blueprint id used by the runner route to start a personal (premium) mock.
const personalMockId = 'personal';

/// Blueprint id used by the runner route to resume the active attempt.
const resumeMockId = 'resume';

final mocksProvider = FutureProvider.autoDispose<List<Mock>>((ref) => ref.watch(apiProvider).mocks());

/// In-progress attempt (if any), offered as a "resume" tile.
final activeAttemptProvider = FutureProvider.autoDispose<Attempt?>((ref) {
  if (ref.watch(authProvider) != AuthStatus.signedIn) return null;
  return ref.watch(apiProvider).activeAttempt();
});

/// Predicted score (null until there is enough history).
final predictionProvider = FutureProvider.autoDispose<Prediction?>((ref) {
  if (ref.watch(authProvider) != AuthStatus.signedIn) return null;
  return ref.watch(apiProvider).prediction();
});

/// Starts (or resumes) an attempt for a runner route id: a blueprint id, [personalMockId] or [resumeMockId].
final attemptProvider = FutureProvider.autoDispose.family<Attempt, String>((ref, id) async {
  final api = ref.watch(apiProvider);
  if (id == resumeMockId) {
    final a = await api.activeAttempt();
    if (a == null) throw StateError('no active attempt');
    return a;
  }
  final lang = await ref.watch(languageCodeProvider.future);
  if (lang == null) throw StateError('no education language');
  if (id == personalMockId) {
    final subjectId = await ref.watch(currentSubjectIdProvider.future);
    if (subjectId == null) throw StateError('no subject');
    return api.startPersonalAttempt(subjectId, lang);
  }
  return api.startAttempt(id, lang);
});

/// Past submitted attempts, newest first.
final historyProvider = FutureProvider.autoDispose<List<HistoryItem>>((ref) {
  if (ref.watch(authProvider) != AuthStatus.signedIn) return const <HistoryItem>[];
  return ref.watch(apiProvider).history();
});

final attemptResultProvider = FutureProvider.autoDispose.family<AttemptResult, String>(
  (ref, id) => ref.watch(apiProvider).attemptResult(id),
);
