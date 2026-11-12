import 'package:firebase_core/firebase_core.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/config.dart';
import 'core/notifications/notification_service.dart';
import 'core/notifications/push_handler.dart';

Future<void> main() async {
  Config.validate();
  WidgetsFlutterBinding.ensureInitialized();
  final notifications = NotificationService();
  await notifications.init();
  var firebaseReady = false;
  try {
    // Uses google-services.json / GoogleService-Info.plist (see README).
    await Firebase.initializeApp();
    firebaseReady = true;
  } catch (_) {
    // App stays usable without Firebase configured.
  }
  if (firebaseReady) {
    await PushHandler.instance.init(notifications);
  }
  runApp(
    ProviderScope(
      overrides: [notificationServiceProvider.overrideWithValue(notifications)],
      child: const DtmApp(),
    ),
  );
}
