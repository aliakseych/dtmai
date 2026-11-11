import 'package:home_widget/home_widget.dart';

import '../config.dart';

/// Pushes streak / daily-goal data to the Android AppWidget and iOS WidgetKit extension.
class WidgetSync {
  bool _ready = false;

  Future<void> _init() async {
    if (_ready) return;
    await HomeWidget.setAppGroupId(Config.appGroupId);
    _ready = true;
  }

  Future<void> update({required int streak, required int dailyXp, required int dailyGoalXp}) async {
    try {
      await _init();
      await HomeWidget.saveWidgetData<int>('streak', streak);
      await HomeWidget.saveWidgetData<int>('daily_xp', dailyXp);
      await HomeWidget.saveWidgetData<int>('daily_goal', dailyGoalXp);
      await HomeWidget.updateWidget(
        androidName: Config.androidWidget,
        iOSName: Config.iosWidget,
      );
    } catch (_) {
      // Widgets are optional; never break the app because of them.
    }
  }
}
