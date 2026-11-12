import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

/// Local notifications: daily streak reminder + display of foreground FCM messages.
class NotificationService {
  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();

  static const _reminderId = 1001;
  static const _oneShotBaseId = 1010;
  static const _skipDays = 7;
  static const _channelId = 'streak_reminder';

  Future<void> init() async {
    tzdata.initializeTimeZones();
    try {
      final zone = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(tz.getLocation(zone.identifier));
    } catch (_) {
      tz.setLocalLocation(tz.getLocation('Asia/Tashkent'));
    }
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );
    await _plugin.initialize(
      settings: const InitializationSettings(android: android, iOS: ios),
    );
  }

  Future<bool> requestPermission() async {
    final ios = _plugin.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>();
    final iosOk = await ios?.requestPermissions(alert: true, badge: true, sound: true);
    final and = _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    final andOk = await and?.requestNotificationsPermission();
    return (iosOk ?? andOk) ?? true;
  }

  NotificationDetails _details(String channelName) => NotificationDetails(
        android: AndroidNotificationDetails(
          _channelId,
          channelName,
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: const DarwinNotificationDetails(),
      );

  /// Schedules streak reminders at [hour]:00 local time. Normally one daily repeating
  /// notification. If [skipToday] (daily goal reached) iOS ignores the start date of a
  /// repeating schedule, so the next 7 days are scheduled as one-shots starting tomorrow;
  /// every sync re-arms them.
  Future<void> scheduleStreakReminder({
    required String title,
    required String body,
    required String channelName,
    int hour = 19,
    bool skipToday = false,
  }) async {
    await cancelStreakReminder();
    final now = tz.TZDateTime.now(tz.local);
    final today = tz.TZDateTime(tz.local, now.year, now.month, now.day, hour);
    if (!skipToday) {
      final at = today.isAfter(now) ? today : today.add(const Duration(days: 1));
      await _plugin.zonedSchedule(
        id: _reminderId,
        title: title,
        body: body,
        scheduledDate: at,
        notificationDetails: _details(channelName),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
        matchDateTimeComponents: DateTimeComponents.time,
      );
      return;
    }
    for (var i = 0; i < _skipDays; i++) {
      final d = tz.TZDateTime(tz.local, now.year, now.month, now.day + 1 + i, hour);
      await _plugin.zonedSchedule(
        id: _oneShotBaseId + i,
        title: title,
        body: body,
        scheduledDate: d,
        notificationDetails: _details(channelName),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      );
    }
  }

  Future<void> cancelStreakReminder() async {
    await _plugin.cancel(id: _reminderId);
    for (var i = 0; i < _skipDays; i++) {
      await _plugin.cancel(id: _oneShotBaseId + i);
    }
  }

  Future<void> showNow({required int id, String? title, String? body, String channelName = 'DTM AI'}) async {
    try {
      await _plugin.show(id: id, title: title, body: body, notificationDetails: _details(channelName));
    } catch (e) {
      debugPrint('notification show failed: $e');
    }
  }
}

final notificationServiceProvider = Provider<NotificationService>(
  (_) => throw UnimplementedError('Overridden in main()'),
);
