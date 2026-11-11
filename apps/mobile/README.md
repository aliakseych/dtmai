# DTM AI — mobile (Flutter)

Learner app for iOS/Android. Locales: uz-Latn (default), uz-Cyrl, ru, en.
Tabs: Learn, Practice, Mocks, Leagues, Profile. Also onboarding (locale, subject, education language,
target lyceum, daily goal, optional placement test), lesson player, timed mock runner, quests,
lyceum explorer, home-screen widgets, local streak reminder and FCM push.

## Accounts: guest-first

- On first launch the app calls `POST /v1/identity/guest` and stores the returned tokens; no sign-up wall.
- Optional email account from the login screen: register, confirm with an email code, sign in.
  Forgot password: `POST /v1/identity/password/forgot` sends a code, then
  `POST /v1/identity/password/reset` (code + new password) signs the user in.
  Errors: 401 `invalid_code`, 422 `weak_password`.
- There is no Telegram login in the app.

## No payments

The app has no checkout, payment links or `url_launcher`. The Premium screen is read-only
(plan, entitlements, subscription status from `GET /v1/me/billing`); subscriptions are managed on the website.

## Setup

```bash
cd apps/mobile
flutter create . --org uz.dtmai --project-name dtmai   # generates android/ and ios/ runners (keeps lib/, pubspec)
flutter pub get
flutter gen-l10n                                       # lib/l10n/app_localizations.dart
flutter run --dart-define=API_URL=https://api.dtm-ai.uz
```

`API_URL` defaults to the production API when omitted (see `lib/core/config.dart`).
There are no build flavors; environments differ only by `--dart-define=API_URL`.

## Push (FCM)

Run `flutterfire configure` or drop in `android/app/google-services.json` and
`ios/Runner/GoogleService-Info.plist`. Without them the app starts and push is skipped.
The device token is registered with `POST /v1/notify/devices`.
On iOS enable Push Notifications + Background Modes (remote notifications) and upload the APNs key.

## Home widgets (home_widget)

Data keys: `streak`, `daily_xp`, `daily_goal`; app group `group.uz.dtmai.app`. Values are synced from
`lib/features/home_sync.dart` using `/v1/me/stats`.

- **Android**: the Kotlin provider, layout and info XML are already under `android/app/src/main`.
  Paste `android/manifest-widget-snippet.xml` into `<application>` of the generated `AndroidManifest.xml`.
  Keep the application id `uz.dtmai.app` (or adjust the package in `StreakWidgetProvider.kt`).
- **iOS**: in Xcode add a *Widget Extension* target named `StreakWidget` (untick Live Activity / Configuration Intent),
  replace its generated sources with `ios/StreakWidget/StreakWidget.swift` + `Info.plist`, and enable the
  App Groups capability `group.uz.dtmai.app` on both `Runner` and `StreakWidget`.

## Notifications

Daily streak reminder (19:00 local, skipped once the daily goal is reached) is scheduled in
`lib/features/home_sync.dart`. Android 13+ asks for POST_NOTIFICATIONS at runtime; add
`android.permission.POST_NOTIFICATIONS`, `RECEIVE_BOOT_COMPLETED` and `SCHEDULE_EXACT_ALARM`/`USE_EXACT_ALARM`
to the manifest, and the flutter_local_notifications boot/schedule receivers per its README.

## API

HTTP goes through `lib/core/api` (dio + auth interceptor with refresh); models are in `lib/core/models.dart`
and follow `apps/api/openapi/openapi.json`. Optional swap to a generated client:
`openapi-generator-cli generate -g dart-dio -i apps/api/openapi/openapi.json`.
