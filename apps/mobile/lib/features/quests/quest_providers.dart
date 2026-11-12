import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';

final questsProvider = FutureProvider.autoDispose<List<Quest>>((ref) => ref.watch(apiProvider).quests());
