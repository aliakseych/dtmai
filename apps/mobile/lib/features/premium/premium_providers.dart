import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api.dart';
import '../../core/models.dart';

final plansProvider = FutureProvider.autoDispose<List<Plan>>((ref) => ref.watch(apiProvider).plans());
