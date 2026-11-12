import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';
import '../../core/locale_controller.dart';
import '../auth/auth_providers.dart';
import '../lyceums/lyceum_providers.dart';
import '../profile/profile_providers.dart';

final subjectsProvider = FutureProvider<List<Subject>>((ref) => ref.watch(apiProvider).subjects());

class SelectedSubject extends Notifier<String?> {
  @override
  String? build() => null;
  void set(String id) => state = id;
}

final selectedSubjectProvider = NotifierProvider<SelectedSubject, String?>(SelectedSubject.new);

/// Selected subject id, defaulting to the first subject.
final currentSubjectIdProvider = FutureProvider<String?>((ref) async {
  final picked = ref.watch(selectedSubjectProvider);
  final subjects = await ref.watch(subjectsProvider.future);
  if (subjects.isEmpty) return null;
  if (picked != null && subjects.any((s) => s.id == picked)) return picked;
  return subjects.first.id;
});

/// Education language chosen by a guest (id).
class GuestLanguage extends Notifier<String?> {
  @override
  String? build() => null;
  void set(String id) => state = id;
}

final guestLanguageProvider = NotifierProvider<GuestLanguage, String?>(GuestLanguage.new);

/// Effective education language: profile → guest choice → UI locale → first.
final currentLanguageProvider = FutureProvider<EduLanguage?>((ref) async {
  final langs = await ref.watch(languagesProvider.future);
  if (langs.isEmpty) return null;
  final me = await ref.watch(meProvider.future);
  final id = me?.educationLanguageId ?? ref.watch(guestLanguageProvider);
  for (final l in langs) {
    if (l.id == id) return l;
  }
  final ui = ref.watch(localeProvider).languageCode;
  for (final l in langs) {
    if (l.code == ui) return l;
  }
  return langs.first;
});

final languageCodeProvider = FutureProvider<String?>((ref) async => (await ref.watch(currentLanguageProvider.future))?.code);

/// Path for the selected subject; null when none is published.
final pathProvider = FutureProvider<LearnerPath?>((ref) async {
  final subjectId = await ref.watch(currentSubjectIdProvider.future);
  final lang = await ref.watch(languageCodeProvider.future);
  if (subjectId == null || lang == null) return null;
  final tag = AppLocales.toTag(ref.watch(localeProvider));
  return ref.watch(apiProvider).path(subjectId, lang, tag);
});

final placementProvider = FutureProvider.family<Placement?, String>((ref, subjectId) async {
  if (ref.watch(authProvider) != AuthStatus.signedIn) return null;
  return ref.watch(apiProvider).placement(subjectId);
});
