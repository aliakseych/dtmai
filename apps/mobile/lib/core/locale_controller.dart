import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/token_storage.dart';

/// Supported UI/content locales. Codes match the API (`uz-Latn`, `uz-Cyrl`, `ru`, `en`).
class AppLocales {
  static const uzLatn = Locale.fromSubtags(languageCode: 'uz', scriptCode: 'Latn');
  static const uzCyrl = Locale.fromSubtags(languageCode: 'uz', scriptCode: 'Cyrl');
  static const ru = Locale('ru');
  static const en = Locale('en');
  static const all = [uzLatn, uzCyrl, ru, en];

  static String toTag(Locale l) =>
      l.scriptCode != null ? '${l.languageCode}-${l.scriptCode}' : l.languageCode;

  static Locale fromTag(String? tag) {
    switch (tag) {
      case 'uz-Cyrl':
        return uzCyrl;
      case 'ru':
        return ru;
      case 'en':
        return en;
      default:
        return uzLatn;
    }
  }

  static String label(Locale l) {
    switch (toTag(l)) {
      case 'uz-Cyrl':
        return 'Ўзбекча';
      case 'ru':
        return 'Русский';
      case 'en':
        return 'English';
      default:
        return 'O‘zbekcha';
    }
  }
}

class LocaleController extends Notifier<Locale> {
  @override
  Locale build() {
    _load();
    return AppLocales.uzLatn;
  }

  Future<void> _load() async {
    final tag = await ref.read(tokenStorageProvider).readLocale();
    if (tag != null) state = AppLocales.fromTag(tag);
  }

  Future<void> set(Locale locale) async {
    state = locale;
    await ref.read(tokenStorageProvider).writeLocale(AppLocales.toTag(locale));
  }
}

final localeProvider = NotifierProvider<LocaleController, Locale>(LocaleController.new);
