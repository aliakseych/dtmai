import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';

/// Education languages (public).
final languagesProvider = FutureProvider<List<EduLanguage>>((ref) => ref.watch(apiProvider).languages());

class LyceumQuery extends Notifier<String> {
  @override
  String build() => '';
  void set(String q) => state = q;
}

final lyceumQueryProvider = NotifierProvider<LyceumQuery, String>(LyceumQuery.new);

final lyceumsProvider = FutureProvider<List<Lyceum>>((ref) {
  final q = ref.watch(lyceumQueryProvider);
  return ref.watch(apiProvider).lyceums(q: q.trim());
});

final lyceumDetailProvider =
    FutureProvider.family<LyceumDetail, String>((ref, id) => ref.watch(apiProvider).lyceum(id));
