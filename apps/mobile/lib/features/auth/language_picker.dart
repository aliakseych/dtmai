import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/locale_controller.dart';

class LanguagePicker extends ConsumerWidget {
  const LanguagePicker({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final current = ref.watch(localeProvider);
    return PopupMenuButton<Locale>(
      icon: const Icon(Icons.language_rounded),
      initialValue: current,
      onSelected: ref.read(localeProvider.notifier).set,
      itemBuilder: (_) => [
        for (final l in AppLocales.all) PopupMenuItem(value: l, child: Text(AppLocales.label(l))),
      ],
    );
  }
}
