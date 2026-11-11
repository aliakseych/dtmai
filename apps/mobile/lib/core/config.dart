/// Build-time configuration: `flutter run --dart-define=API_URL=https://api.dtm-ai.uz`.
class Config {
  static const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'https://api.dtm-ai.uz');
  static const appGroupId = 'group.uz.dtmai.app';
  static const androidWidget = 'StreakWidgetProvider';
  static const iosWidget = 'StreakWidget';
}
