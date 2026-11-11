import 'package:flutter/widgets.dart';

import '../l10n/app_localizations.dart';
import 'locale_controller.dart';

extension L10nContext on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);

  /// API locale tag (`uz-Latn`, `uz-Cyrl`, `ru`, `en`) of the active UI locale.
  String get localeTag => AppLocales.toTag(Localizations.localeOf(this));
}
