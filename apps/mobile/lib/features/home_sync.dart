import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api/api.dart';
import '../core/home_widget/widget_sync.dart';
import '../core/locale_controller.dart';
import '../core/notifications/notification_service.dart';
import '../core/notifications/push_handler.dart';
import '../l10n/app_localizations.dart';
import 'auth/auth_providers.dart';
import 'profile/profile_providers.dart';

final widgetSyncProvider = Provider<WidgetSync>((_) => WidgetSync());

/// Mirrors `/v1/me/stats` to home-screen widgets, (re)schedules the local streak
/// reminder in the active locale and registers the FCM token. Watched once from [DtmApp].
final homeSyncProvider = Provider<void>((ref) {
  String? registeredToken;

  Future<void> registerPush() async {
    try {
      final token = await PushHandler.instance.token();
      if (token == null || token == registeredToken) return;
      final platform = defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android';
      await ref.read(apiProvider).registerDevice(platform, token);
      registeredToken = token;
    } catch (_) {
      // Push is optional (Firebase may be unconfigured); retried on the next sync.
    }
  }

  Future<void> sync() async {
    final stats = ref.read(statsProvider).value;
    if (ref.read(authProvider) != AuthStatus.signedIn || stats == null) return;
    await ref.read(widgetSyncProvider).update(
          streak: stats.streak,
          dailyXp: stats.todayXp,
          dailyGoalXp: stats.dailyGoalXp,
        );
    // Ask for notification permission only after onboarding (not on the first launch).
    final me = ref.read(meProvider).value;
    final onboarded = me != null &&
        (me.educationLanguageId != null || me.dreamLyceumIds.isNotEmpty || ref.read(onboardingSkippedProvider));
    if (!onboarded) return;
    final notifications = ref.read(notificationServiceProvider);
    await notifications.requestPermission();
    await PushHandler.instance.requestPermission();
    final t = lookupAppLocalizations(ref.read(localeProvider));
    await notifications.scheduleStreakReminder(
      title: t.streakReminderTitle,
      body: t.streakReminderBody,
      channelName: t.reminderChannel,
      skipToday: stats.todayXp >= stats.dailyGoalXp,
    );
    await registerPush();
  }

  ref.listen(statsProvider, (_, __) => sync());
  ref.listen(meProvider, (_, __) => sync());
  ref.listen(onboardingSkippedProvider, (_, __) => sync());
  ref.listen(localeProvider, (_, __) => sync());
  ref.listen(authProvider, (_, next) {
    if (next == AuthStatus.signedOut) {
      registeredToken = null;
      ref.read(notificationServiceProvider).cancelStreakReminder();
    }
  });
});
