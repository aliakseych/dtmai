import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_ru.dart';
import 'app_localizations_uz.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('ru'),
    Locale('uz'),
    Locale.fromSubtags(languageCode: 'uz', scriptCode: 'Cyrl'),
    Locale.fromSubtags(languageCode: 'uz', scriptCode: 'Latn'),
  ];

  /// No description provided for @appName.
  ///
  /// In uz_Latn, this message translates to:
  /// **'DTM AI'**
  String get appName;

  /// No description provided for @continueLabel.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Davom etish'**
  String get continueLabel;

  /// No description provided for @check.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tekshirish'**
  String get check;

  /// No description provided for @skip.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘tkazib yuborish'**
  String get skip;

  /// No description provided for @correct.
  ///
  /// In uz_Latn, this message translates to:
  /// **'To‘g‘ri!'**
  String get correct;

  /// No description provided for @incorrect.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Noto‘g‘ri'**
  String get incorrect;

  /// No description provided for @correctAnswer.
  ///
  /// In uz_Latn, this message translates to:
  /// **'To‘g‘ri javob:'**
  String get correctAnswer;

  /// No description provided for @explanation.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tushuntirish'**
  String get explanation;

  /// No description provided for @signIn.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kirish'**
  String get signIn;

  /// No description provided for @email.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @sendCode.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kod yuborish'**
  String get sendCode;

  /// No description provided for @code.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tasdiqlash kodi'**
  String get code;

  /// No description provided for @verify.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tasdiqlash'**
  String get verify;

  /// No description provided for @orLabel.
  ///
  /// In uz_Latn, this message translates to:
  /// **'yoki'**
  String get orLabel;

  /// No description provided for @onboardingTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Maqsadingizni tanlang'**
  String get onboardingTitle;

  /// No description provided for @chooseLyceum.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Litsey'**
  String get chooseLyceum;

  /// No description provided for @chooseLanguage.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Ta’lim tili'**
  String get chooseLanguage;

  /// No description provided for @startPlacement.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Saralash testini boshlash'**
  String get startPlacement;

  /// No description provided for @learn.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘rganish'**
  String get learn;

  /// No description provided for @practice.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Mashq'**
  String get practice;

  /// No description provided for @mocks.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Mock testlar'**
  String get mocks;

  /// No description provided for @leagues.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Ligalar'**
  String get leagues;

  /// No description provided for @quests.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Topshiriqlar'**
  String get quests;

  /// No description provided for @profile.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Profil'**
  String get profile;

  /// No description provided for @premium.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Premium'**
  String get premium;

  /// No description provided for @lyceums.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Litseylar'**
  String get lyceums;

  /// No description provided for @hearts.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yuraklar'**
  String get hearts;

  /// No description provided for @noHearts.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yuraklar tugadi. Birozdan so‘ng qayting yoki Premium oling.'**
  String get noHearts;

  /// No description provided for @streakDays.
  ///
  /// In uz_Latn, this message translates to:
  /// **'{n} kunlik seriya'**
  String streakDays(int n);

  /// No description provided for @gems.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Olmoslar'**
  String get gems;

  /// No description provided for @xp.
  ///
  /// In uz_Latn, this message translates to:
  /// **'XP'**
  String get xp;

  /// No description provided for @dailyGoal.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kunlik maqsad'**
  String get dailyGoal;

  /// No description provided for @mistakes.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Xatolar ustida ishlash'**
  String get mistakes;

  /// No description provided for @weakTopics.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Zaif mavzular'**
  String get weakTopics;

  /// No description provided for @bankDrill.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Savollar banki'**
  String get bankDrill;

  /// No description provided for @personalMock.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Shaxsiy mock'**
  String get personalMock;

  /// No description provided for @start.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Boshlash'**
  String get start;

  /// No description provided for @submit.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Topshirish'**
  String get submit;

  /// No description provided for @finish.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yakunlash'**
  String get finish;

  /// No description provided for @timeLeft.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Qolgan vaqt'**
  String get timeLeft;

  /// No description provided for @markReview.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Belgilash'**
  String get markReview;

  /// No description provided for @navigator.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Savollar xaritasi'**
  String get navigator;

  /// No description provided for @answeredCount.
  ///
  /// In uz_Latn, this message translates to:
  /// **'{a} / {t} javob berildi'**
  String answeredCount(int a, int t);

  /// No description provided for @score.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Natija'**
  String get score;

  /// No description provided for @predictedScore.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Taxminiy ball'**
  String get predictedScore;

  /// No description provided for @lessonComplete.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Dars yakunlandi!'**
  String get lessonComplete;

  /// No description provided for @dailyQuests.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kunlik topshiriqlar'**
  String get dailyQuests;

  /// No description provided for @weeklyLeague.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Haftalik liga'**
  String get weeklyLeague;

  /// No description provided for @rank.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘rin'**
  String get rank;

  /// No description provided for @friends.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Do‘stlar'**
  String get friends;

  /// No description provided for @logout.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Chiqish'**
  String get logout;

  /// No description provided for @language.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Til'**
  String get language;

  /// No description provided for @retry.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Qayta urinish'**
  String get retry;

  /// No description provided for @errorGeneric.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Xatolik yuz berdi'**
  String get errorGeneric;

  /// No description provided for @empty.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Hozircha hech narsa yo‘q'**
  String get empty;

  /// No description provided for @typeAnswer.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Javobni kiriting'**
  String get typeAnswer;

  /// No description provided for @premiumPerks.
  ///
  /// In uz_Latn, this message translates to:
  /// **'AI tushuntirishlar, AI repetitor, shaxsiy mocklar va tahlil'**
  String get premiumPerks;

  /// No description provided for @quota.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kvota'**
  String get quota;

  /// No description provided for @applications.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Arizalar'**
  String get applications;

  /// No description provided for @competition.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Konkurs'**
  String get competition;

  /// No description provided for @year.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yil'**
  String get year;

  /// No description provided for @search.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Qidirish'**
  String get search;

  /// No description provided for @previousYears.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘tgan yillar'**
  String get previousYears;

  /// No description provided for @streakReminderTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriyani yo‘qotmang!'**
  String get streakReminderTitle;

  /// No description provided for @streakReminderBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bugungi darsni bajaring — Temur sizni kutmoqda.'**
  String get streakReminderBody;

  /// No description provided for @reminderChannel.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Eslatmalar'**
  String get reminderChannel;

  /// No description provided for @password.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Parol'**
  String get password;

  /// No description provided for @nameLabel.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Ism'**
  String get nameLabel;

  /// No description provided for @signUp.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Ro‘yxatdan o‘tish'**
  String get signUp;

  /// No description provided for @haveAccount.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Akkauntingiz bormi? Kirish'**
  String get haveAccount;

  /// No description provided for @noAccount.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Akkauntingiz yo‘qmi? Ro‘yxatdan o‘ting'**
  String get noAccount;

  /// No description provided for @notNow.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Hozir emas'**
  String get notNow;

  /// No description provided for @resendCode.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kodni qayta yuborish'**
  String get resendCode;

  /// No description provided for @verifyPrompt.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Emailga yuborilgan kodni kiriting'**
  String get verifyPrompt;

  /// No description provided for @guestGateMessage.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bu imkoniyatdan foydalanish uchun akkaunt yarating'**
  String get guestGateMessage;

  /// No description provided for @skipPlacement.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Saralash testini o‘tkazib yuborish'**
  String get skipPlacement;

  /// No description provided for @placementBannerTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Saralash testidan o‘ting'**
  String get placementBannerTitle;

  /// No description provided for @placementBannerBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yo‘lni darajangizga moslaymiz'**
  String get placementBannerBody;

  /// No description provided for @noPath.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bu fan uchun hali yo‘l yo‘q'**
  String get noPath;

  /// No description provided for @noFriends.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Hali do‘stlar yo‘q'**
  String get noFriends;

  /// No description provided for @streakLabel.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriya'**
  String get streakLabel;

  /// No description provided for @planPremium.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Premium faol'**
  String get planPremium;

  /// No description provided for @planFree.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bepul tarif'**
  String get planFree;

  /// No description provided for @reviewToEarn.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yuraklar olish uchun xatolar ustida ishlang'**
  String get reviewToEarn;

  /// No description provided for @waitForRefill.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yoki yuraklar tiklanishini kuting'**
  String get waitForRefill;

  /// No description provided for @heartsBanner.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yuraklar tugadi'**
  String get heartsBanner;

  /// No description provided for @exitConfirmTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Darsdan chiqasizmi?'**
  String get exitConfirmTitle;

  /// No description provided for @exitConfirmBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bu darsdagi jarayon yo‘qoladi.'**
  String get exitConfirmBody;

  /// No description provided for @cancel.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bekor qilish'**
  String get cancel;

  /// No description provided for @leave.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Chiqish'**
  String get leave;

  /// No description provided for @placementDone.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Saralash tugadi! Yo‘lingiz tayyor.'**
  String get placementDone;

  /// No description provided for @accuracy.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Aniqlik'**
  String get accuracy;

  /// No description provided for @resumeAttempt.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Imtihonni davom ettirish'**
  String get resumeAttempt;

  /// No description provided for @submitConfirmTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Imtihonni topshirasizmi?'**
  String get submitConfirmTitle;

  /// No description provided for @exitMockTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Imtihondan chiqasizmi?'**
  String get exitMockTitle;

  /// No description provided for @exitMockBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Javoblar saqlandi; vaqt tugamaguncha davom ettirishingiz mumkin.'**
  String get exitMockBody;

  /// No description provided for @autosaveFailed.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Javoblarni saqlab bo‘lmadi'**
  String get autosaveFailed;

  /// No description provided for @onTrack.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘tish baliga yaqinsiz'**
  String get onTrack;

  /// No description provided for @offTrack.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘tish balidan past'**
  String get offTrack;

  /// No description provided for @passingScore.
  ///
  /// In uz_Latn, this message translates to:
  /// **'O‘tish bali'**
  String get passingScore;

  /// No description provided for @gap.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Farq'**
  String get gap;

  /// No description provided for @setTarget.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Maqsad qilish'**
  String get setTarget;

  /// No description provided for @premiumWebOnly.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Obuna saytimizda rasmiylashtiriladi'**
  String get premiumWebOnly;

  /// No description provided for @monthsShort.
  ///
  /// In uz_Latn, this message translates to:
  /// **'oy'**
  String get monthsShort;

  /// No description provided for @chooseSubject.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Fan'**
  String get chooseSubject;

  /// No description provided for @planActive.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Premium {date} gacha'**
  String planActive(String date);

  /// No description provided for @refillIn.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Keyingi yurak {time} dan keyin'**
  String refillIn(String time);

  /// No description provided for @leagueEndsIn.
  ///
  /// In uz_Latn, this message translates to:
  /// **'{time} dan keyin tugaydi'**
  String leagueEndsIn(String time);

  /// No description provided for @submitConfirmBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Javobsiz: {unanswered}, belgilangan: {flagged}. Baribir topshirasizmi?'**
  String submitConfirmBody(int unanswered, int flagged);

  /// No description provided for @forgotPassword.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Parolni unutdingizmi?'**
  String get forgotPassword;

  /// No description provided for @resetPassword.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Parolni tiklash'**
  String get resetPassword;

  /// No description provided for @newPassword.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yangi parol'**
  String get newPassword;

  /// No description provided for @resetPrompt.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Emaildagi kodni va yangi parolni kiriting'**
  String get resetPrompt;

  /// No description provided for @invalidCode.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kod noto‘g‘ri yoki eskirgan'**
  String get invalidCode;

  /// No description provided for @weakPassword.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Parol juda oddiy'**
  String get weakPassword;

  /// No description provided for @allTime.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Barcha vaqt'**
  String get allTime;

  /// No description provided for @answersNotAccepted.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Vaqt tugadi – oxirgi javoblar qabul qilinmadi. Ish topshirilmoqda.'**
  String get answersNotAccepted;

  /// No description provided for @audioFailed.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Audioni ijro etib bo‘lmadi'**
  String get audioFailed;

  /// No description provided for @channelEmail.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Email'**
  String get channelEmail;

  /// No description provided for @channelPush.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Push'**
  String get channelPush;

  /// No description provided for @channelTelegram.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Telegram'**
  String get channelTelegram;

  /// No description provided for @drillWeakTopics.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Zaif mavzularni mashq qilish'**
  String get drillWeakTopics;

  /// No description provided for @explain.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tushuntirish'**
  String get explain;

  /// No description provided for @freezeUsed.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriya muzlatildi'**
  String get freezeUsed;

  /// No description provided for @guestLogoutTitle.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Mehmon rejimidan chiqasizmi?'**
  String get guestLogoutTitle;

  /// No description provided for @guestLogoutBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yutuqlaringiz akkauntga bog‘lanmagan va yo‘qoladi.'**
  String get guestLogoutBody;

  /// No description provided for @history.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tarix'**
  String get history;

  /// No description provided for @kindDailyQuestion.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kun savoli'**
  String get kindDailyQuestion;

  /// No description provided for @kindLeagueEnding.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Liga tugayapti'**
  String get kindLeagueEnding;

  /// No description provided for @kindStreakReminder.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriya eslatmasi'**
  String get kindStreakReminder;

  /// No description provided for @listen.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tinglash'**
  String get listen;

  /// No description provided for @maxPerDay.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kuniga ko‘pi bilan'**
  String get maxPerDay;

  /// No description provided for @mergeFailed.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Kirildi, lekin mehmon yutuqlarini birlashtirib bo‘lmadi'**
  String get mergeFailed;

  /// No description provided for @noReviewDue.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Hozir takrorlash uchun hech narsa yo‘q'**
  String get noReviewDue;

  /// No description provided for @notAnswered.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Javob berilmagan'**
  String get notAnswered;

  /// No description provided for @notificationSettings.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bildirishnomalar'**
  String get notificationSettings;

  /// No description provided for @pauseAudio.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Pauza'**
  String get pauseAudio;

  /// No description provided for @playAudio.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Ijro etish'**
  String get playAudio;

  /// No description provided for @quietHours.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Tinch soatlar'**
  String get quietHours;

  /// No description provided for @reportQuestion.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Xato haqida xabar berish'**
  String get reportQuestion;

  /// No description provided for @reportReason.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bu savolda nima noto‘g‘ri?'**
  String get reportReason;

  /// No description provided for @reportSent.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Rahmat, xabar yuborildi'**
  String get reportSent;

  /// No description provided for @reviewAnswers.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Javoblar tahlili'**
  String get reviewAnswers;

  /// No description provided for @save.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Saqlash'**
  String get save;

  /// No description provided for @saveProgress.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yutuqlaringizni saqlang'**
  String get saveProgress;

  /// No description provided for @saveProgressBody.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriya va XP yo‘qolmasligi uchun kiring yoki akkaunt yarating.'**
  String get saveProgressBody;

  /// No description provided for @saved.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Saqlandi'**
  String get saved;

  /// No description provided for @send.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yuborish'**
  String get send;

  /// No description provided for @sessionExpired.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seans tugadi. Qayta kiring.'**
  String get sessionExpired;

  /// No description provided for @streakAtRisk.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriyangiz xavf ostida – bugun mashq qiling!'**
  String get streakAtRisk;

  /// No description provided for @tabFriends.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Do‘stlar'**
  String get tabFriends;

  /// No description provided for @tabLeague.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Liga'**
  String get tabLeague;

  /// No description provided for @tabLyceum.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Litsey'**
  String get tabLyceum;

  /// No description provided for @useFreeze.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Muzlatish'**
  String get useFreeze;

  /// No description provided for @weekly.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Hafta'**
  String get weekly;

  /// No description provided for @yourAnswer.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Sizning javobingiz'**
  String get yourAnswer;

  /// No description provided for @minutesShort.
  ///
  /// In uz_Latn, this message translates to:
  /// **'{n} daq'**
  String minutesShort(int n);

  /// No description provided for @durationDaysHours.
  ///
  /// In uz_Latn, this message translates to:
  /// **'{days}k {hours}s'**
  String durationDaysHours(int days, int hours);

  /// No description provided for @durationHoursMinutes.
  ///
  /// In uz_Latn, this message translates to:
  /// **'{hours}s {minutes}d'**
  String durationHoursMinutes(int hours, int minutes);

  /// No description provided for @streakFreezes.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Seriya muzlatgichlari: {n}'**
  String streakFreezes(int n);

  /// No description provided for @chooseCity.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Shahar'**
  String get chooseCity;

  /// No description provided for @cityHint.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yoki o\'qishni rejalashtirgan shahringiz. Turli shaharlarda o\'qishga tayyor bo\'lsangiz, tanlamang.'**
  String get cityHint;

  /// No description provided for @anyCity.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Istalgan shahar'**
  String get anyCity;

  /// No description provided for @chooseSubjects.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Fanlar (bir yoki bir nechta)'**
  String get chooseSubjects;

  /// No description provided for @dormitory.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yotoqxona'**
  String get dormitory;

  /// No description provided for @dormitoryAvailable.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yotoqxona bor'**
  String get dormitoryAvailable;

  /// No description provided for @dormitoryLimited.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yotoqxona o\'rinlari cheklangan'**
  String get dormitoryLimited;

  /// No description provided for @dormitoryNone.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yotoqxona yo\'q'**
  String get dormitoryNone;

  /// No description provided for @dormitoryUnknown.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yotoqxona haqida ma\'lumot yo\'q'**
  String get dormitoryUnknown;

  /// No description provided for @dreamLyceums.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Orzudagi litseylarim'**
  String get dreamLyceums;

  /// No description provided for @dreamRules.
  ///
  /// In uz_Latn, this message translates to:
  /// **'3 tagacha litseyni ustuvorlik tartibida tanlash mumkin. Balingiz avval 1-tanlov bilan solishtiriladi. Yetarli bo\'lsa, o\'sha yerga qabul qilinasiz, 2- va 3-tanlov ko\'rib chiqilmaydi. Yetmasa, 2-tanlov, keyin 3-tanlov tekshiriladi. Birortasi ham to\'g\'ri kelmasa, natijangiz 1-tanlov bo\'yicha ko\'rsatiladi. Haqiqiy orzuingizni birinchi, ishonchliroq variantni uchinchi qo\'ying.'**
  String get dreamRules;

  /// No description provided for @moveUp.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Yuqoriga'**
  String get moveUp;

  /// No description provided for @moveDown.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Pastga'**
  String get moveDown;

  /// No description provided for @removeItem.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Olib tashlash'**
  String get removeItem;

  /// No description provided for @emptySlot.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Bo\'sh o\'rin'**
  String get emptySlot;

  /// No description provided for @addToDreams.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Orzularimga qo\'shish'**
  String get addToDreams;

  /// No description provided for @removeFromDreams.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Orzularimdan olib tashlash'**
  String get removeFromDreams;

  /// No description provided for @addLyceum.
  ///
  /// In uz_Latn, this message translates to:
  /// **'Litsey qo\'shish'**
  String get addLyceum;

  /// No description provided for @tooManyDreams.
  ///
  /// In uz_Latn, this message translates to:
  /// **'3 tagacha litsey tanlash mumkin.'**
  String get tooManyDreams;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'ru', 'uz'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when language+script codes are specified.
  switch (locale.languageCode) {
    case 'uz':
      {
        switch (locale.scriptCode) {
          case 'Cyrl':
            return AppLocalizationsUzCyrl();
          case 'Latn':
            return AppLocalizationsUzLatn();
        }
        break;
      }
  }

  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'ru':
      return AppLocalizationsRu();
    case 'uz':
      return AppLocalizationsUz();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
