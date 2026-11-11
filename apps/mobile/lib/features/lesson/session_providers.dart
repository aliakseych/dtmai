import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';
import '../learn/learn_providers.dart';

/// `mode` is `lesson|placement|review|drill`. For `lesson` [refId] is the lesson id;
/// for the others it is the subject id (or `current` for the selected subject).
typedef SessionArgs = ({String mode, String? refId, String? topicId, String? typeId});

/// A started session. Auto-disposed when the screen is popped.
final sessionProvider = FutureProvider.autoDispose.family<SessionData, SessionArgs>((ref, a) async {
  final api = ref.watch(apiProvider);
  final lang = await ref.watch(languageCodeProvider.future);
  if (lang == null) throw StateError('no education language');
  if (a.mode == 'lesson') return api.startLesson(a.refId!, lang);
  final subjectId = (a.refId == null || a.refId == 'current') ? await ref.read(currentSubjectIdProvider.future) : a.refId;
  if (subjectId == null) throw StateError('no subject');
  return switch (a.mode) {
    'placement' => api.startPlacement(subjectId, lang),
    'review' => api.startReview(subjectId, lang),
    _ => api.startDrill(subjectId, lang, topicId: a.topicId, typeId: a.typeId),
  };
});

/// Reading passage shared by several questions.
final passageProvider = FutureProvider.autoDispose.family<Passage, String>(
  (ref, id) => ref.watch(apiProvider).passage(id),
);
