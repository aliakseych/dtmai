import 'package:flutter/foundation.dart' show kReleaseMode;

/// Build-time configuration: `flutter run --dart-define=API_URL=https://api.dtm-ai.uz`.
class Config {
  static const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'https://api.dtm-ai.uz');
  /// Public base for media keys; empty means the API origin.
  static const mediaUrl = String.fromEnvironment('MEDIA_URL', defaultValue: '');
  static const appGroupId = 'group.uz.dtmai.app';
  static const androidWidget = 'StreakWidgetProvider';
  static const iosWidget = 'StreakWidget';

  /// Fails fast on insecure release configuration; call from main().
  static void validate({String api = apiUrl, bool release = kReleaseMode}) {
    if (release && Uri.parse(api).scheme != 'https') {
      throw StateError('API_URL must use https in release builds: $api');
    }
  }
}

