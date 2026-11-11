import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';
import '../learn/learn_providers.dart';

/// Mistakes due for spaced review in the selected subject.
final reviewDueProvider = FutureProvider.autoDispose<int>((ref) async {
  final subjectId = await ref.watch(currentSubjectIdProvider.future);
  if (subjectId == null) return 0;
  return ref.watch(apiProvider).reviewDue(subjectId);
});

/// Weakest topics / question types in the selected subject.
final weakAreasProvider = FutureProvider.autoDispose<List<WeakArea>>((ref) async {
  final subjectId = await ref.watch(currentSubjectIdProvider.future);
  if (subjectId == null) return const [];
  return ref.watch(apiProvider).weakAreas(subjectId);
});
