---
name: flutter
description: Use for apps/mobile Flutter work: screens, API client, widgets, notifications.
---

# Flutter
- App in `apps/mobile`. API client generated with openapi-generator `dart-dio` from `apps/api/openapi/openapi.json`; never hand-write models.
- Mirror `packages/ui` tokens (see `ui-ux`). Locales: uz-Latn, uz-Cyrl, ru, en via ARB files with parity.
- Home widgets via `home_widget` (streak + daily goal); push via FCM, local reminders via `flutter_local_notifications`.
- `dart format .`, `flutter analyze`, `flutter test` before finishing.
