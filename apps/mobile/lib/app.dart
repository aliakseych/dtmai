import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/locale_controller.dart';
import 'features/home_sync.dart';
import 'l10n/app_localizations.dart';
import 'router.dart';
import 'theme/app_theme.dart';

class DtmApp extends ConsumerWidget {
  const DtmApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(homeSyncProvider);
    final router = ref.watch(routerProvider);
    final locale = ref.watch(localeProvider);
    return MaterialApp.router(
      title: 'DTM AI',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      routerConfig: router,
      locale: locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: [AppLocalizations.delegate, ...GlobalMaterialLocalizations.delegates],
    );
  }
}
