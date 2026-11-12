import 'package:firebase_messaging/firebase_messaging.dart';

import 'notification_service.dart';

@pragma('vm:entry-point')
Future<void> firebaseBackgroundHandler(RemoteMessage message) async {
  // Notification payloads are shown by the OS while backgrounded; nothing to do.
}

/// FCM wiring: permission, background handler, foreground display.
class PushHandler {
  PushHandler._();
  static final instance = PushHandler._();

  Future<void> init(NotificationService local) async {
    FirebaseMessaging.onBackgroundMessage(firebaseBackgroundHandler);
    FirebaseMessaging.onMessage.listen((m) {
      final n = m.notification;
      if (n == null) return;
      local.showNow(id: m.hashCode, title: n.title, body: n.body);
    });
  }

  /// Asks for the OS push permission; called only once the learner finished onboarding.
  Future<void> requestPermission() async {
    await FirebaseMessaging.instance.requestPermission();
  }

  /// Token to register with the API (`POST /v1/notify/devices`).
  Future<String?> token() => FirebaseMessaging.instance.getToken();
}
