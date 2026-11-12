import 'package:dtmai/l10n/app_localizations.dart';
import 'package:dtmai/theme/app_theme.dart';
import 'package:dtmai/widgets/logo.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';

void main() {
  testWidgets('themed localized app shell builds for every locale', (t) async {
    for (final locale in AppLocalizations.supportedLocales) {
      await t.pumpWidget(ProviderScope(
        child: MaterialApp(
          theme: buildAppTheme(),
          locale: locale,
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: [AppLocalizations.delegate, ...GlobalMaterialLocalizations.delegates],
          home: Builder(
            builder: (c) => Scaffold(body: Column(children: [const Logo(), Text(AppLocalizations.of(c).appName)])),
          ),
        ),
      ));
      await t.pump();
      expect(find.text(AppLocalizations.of(t.element(find.byType(Logo))).appName), findsOneWidget, reason: '$locale');
      expect(find.byType(Logo), findsOneWidget);
    }
  });
}
