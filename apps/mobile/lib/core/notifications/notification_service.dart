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

  /// Schedules the next reminder at [hour]:00 local time. If [skipToday] (daily goal
  /// already reached) the first reminder is tomorrow.
  Future<void> scheduleStreakReminder({
    required String title,
    required String body,
    required String channelName,
    int hour = 19,
    bool skipToday = false,
  }) async {
    await _plugin.cancel(id: _reminderId);
    final now = tz.TZDateTime.now(tz.local);
    var at = tz.TZDateTime(tz.local, now.year, now.month, now.day, hour);
    if (skipToday || !at.isAfter(now)) at = at.add(const Duration(days: 1));
    await _plugin.zonedSchedule(
      id: _reminderId,
      title: title,
      body: body,
      scheduledDate: at,
      notificationDetails: _details(channelName),
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.time,
    );
  }

  Future<void> cancelStreakReminder() => _plugin.cancel(id: _reminderId);

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
