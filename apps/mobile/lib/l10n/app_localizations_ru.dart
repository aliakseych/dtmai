// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get appName => 'ДТМ AI';

  @override
  String get continueLabel => 'Продолжить';

  @override
  String get check => 'Проверить';

  @override
  String get skip => 'Пропустить';

  @override
  String get correct => 'Верно!';

  @override
  String get incorrect => 'Неверно';

  @override
  String get correctAnswer => 'Правильный ответ:';

  @override
  String get explanation => 'Объяснение';

  @override
  String get signIn => 'Войти';

  @override
  String get email => 'Email';

  @override
  String get sendCode => 'Отправить код';

  @override
  String get code => 'Код подтверждения';

  @override
  String get verify => 'Подтвердить';

  @override
  String get orLabel => 'или';

  @override
  String get onboardingTitle => 'Выберите цель';

  @override
  String get chooseLyceum => 'Лицей';

  @override
  String get chooseLanguage => 'Язык обучения';

  @override
  String get startPlacement => 'Начать вступительный тест';

  @override
  String get learn => 'Учёба';

  @override
  String get practice => 'Практика';

  @override
  String get mocks => 'Пробные тесты';

  @override
  String get leagues => 'Лиги';

  @override
  String get quests => 'Задания';

  @override
  String get profile => 'Профиль';

  @override
  String get premium => 'Premium';

  @override
  String get lyceums => 'Лицеи';

  @override
  String get hearts => 'Сердца';

  @override
  String get noHearts =>
      'Сердца закончились. Вернитесь позже или оформите Premium.';

  @override
  String streakDays(int n) {
    return 'Серия: $n дн.';
  }

  @override
  String get gems => 'Кристаллы';

  @override
  String get xp => 'XP';

  @override
  String get dailyGoal => 'Дневная цель';

  @override
  String get mistakes => 'Работа над ошибками';

  @override
  String get weakTopics => 'Слабые темы';

  @override
  String get bankDrill => 'Банк вопросов';

  @override
  String get personalMock => 'Персональный пробный';

  @override
  String get start => 'Начать';

  @override
  String get submit => 'Сдать';

  @override
  String get finish => 'Завершить';

  @override
  String get timeLeft => 'Осталось времени';

  @override
  String get markReview => 'Отметить';

  @override
  String get navigator => 'Навигатор';

  @override
  String answeredCount(int a, int t) {
    return 'Отвечено: $a из $t';
  }

  @override
  String get score => 'Результат';

  @override
  String get predictedScore => 'Прогнозируемый балл';

  @override
  String get lessonComplete => 'Урок пройден!';

  @override
  String get dailyQuests => 'Ежедневные задания';

  @override
  String get weeklyLeague => 'Недельная лига';

  @override
  String get rank => 'Место';

  @override
  String get friends => 'Друзья';

  @override
  String get logout => 'Выйти';

  @override
  String get language => 'Язык';

  @override
  String get retry => 'Повторить';

  @override
  String get errorGeneric => 'Что-то пошло не так';

  @override
  String get empty => 'Пока ничего нет';

  @override
  String get typeAnswer => 'Введите ответ';

  @override
  String get premiumPerks =>
      'ИИ-объяснения, ИИ-репетитор, персональные пробные и аналитика';

  @override
  String get quota => 'Квота';

  @override
  String get applications => 'Заявки';

  @override
  String get competition => 'Конкурс';

  @override
  String get year => 'Год';

  @override
  String get search => 'Поиск';

  @override
  String get previousYears => 'Прошлые годы';

  @override
  String get streakReminderTitle => 'Не потеряйте серию!';

  @override
  String get streakReminderBody =>
      'Пройдите сегодняшний урок — Темур ждёт вас.';

  @override
  String get reminderChannel => 'Напоминания';

  @override
  String get password => 'Пароль';

  @override
  String get nameLabel => 'Имя';

  @override
  String get signUp => 'Регистрация';

  @override
  String get haveAccount => 'Уже есть аккаунт? Войти';

  @override
  String get noAccount => 'Нет аккаунта? Зарегистрироваться';

  @override
  String get notNow => 'Не сейчас';

  @override
  String get resendCode => 'Отправить код ещё раз';

  @override
  String get verifyPrompt => 'Введите код из письма';

  @override
  String get guestGateMessage => 'Создайте аккаунт, чтобы пользоваться этим';

  @override
  String get skipPlacement => 'Пропустить тест';

  @override
  String get placementBannerTitle => 'Пройдите входной тест';

  @override
  String get placementBannerBody => 'Мы подберём путь под ваш уровень';

  @override
  String get noPath => 'Для этого предмета пока нет пути';

  @override
  String get noFriends => 'Друзей пока нет';

  @override
  String get streakLabel => 'Серия';

  @override
  String get planPremium => 'Premium активен';

  @override
  String get planFree => 'Бесплатный тариф';

  @override
  String get reviewToEarn => 'Поработайте над ошибками, чтобы получить сердца';

  @override
  String get waitForRefill => 'Или дождитесь восстановления сердец';

  @override
  String get heartsBanner => 'Сердца закончились';

  @override
  String get exitConfirmTitle => 'Выйти из урока?';

  @override
  String get exitConfirmBody => 'Прогресс этого урока будет потерян.';

  @override
  String get cancel => 'Отмена';

  @override
  String get leave => 'Выйти';

  @override
  String get placementDone => 'Тест пройден! Ваш путь готов.';

  @override
  String get accuracy => 'Точность';

  @override
  String get resumeAttempt => 'Продолжить экзамен';

  @override
  String get submitConfirmTitle => 'Сдать экзамен?';

  @override
  String get exitMockTitle => 'Выйти из экзамена?';

  @override
  String get exitMockBody =>
      'Ответы сохранены; вы сможете продолжить, пока идёт время.';

  @override
  String get autosaveFailed => 'Не удалось сохранить ответы';

  @override
  String get onTrack => 'Вы на пути к проходному баллу';

  @override
  String get offTrack => 'Ниже проходного балла';

  @override
  String get passingScore => 'Проходной балл';

  @override
  String get gap => 'Разница';

  @override
  String get setTarget => 'Сделать целью';

  @override
  String get premiumWebOnly => 'Подписка оформляется на сайте';

  @override
  String get monthsShort => 'мес.';

  @override
  String get chooseSubject => 'Предмет';

  @override
  String planActive(String date) {
    return 'Premium до $date';
  }

  @override
  String refillIn(String time) {
    return 'Следующее сердце через $time';
  }

  @override
  String leagueEndsIn(String time) {
    return 'Закончится через $time';
  }

  @override
  String submitConfirmBody(int unanswered, int flagged) {
    return 'Без ответа: $unanswered, отмечено: $flagged. Всё равно сдать?';
  }

  @override
  String get forgotPassword => 'Забыли пароль?';

  @override
  String get resetPassword => 'Сбросить пароль';

  @override
  String get newPassword => 'Новый пароль';

  @override
  String get resetPrompt => 'Введите код из письма и новый пароль';

  @override
  String get invalidCode => 'Неверный или просроченный код';

  @override
  String get weakPassword => 'Слишком простой пароль';

  @override
  String get allTime => 'За всё время';

  @override
  String get answersNotAccepted =>
      'Время вышло — последние ответы не приняты. Отправляем работу.';

  @override
  String get audioFailed => 'Не удалось воспроизвести аудио';

  @override
  String get channelEmail => 'Почта';

  @override
  String get channelPush => 'Push';

  @override
  String get channelTelegram => 'Telegram';

  @override
  String get drillWeakTopics => 'Тренировать слабые темы';

  @override
  String get explain => 'Объяснить';

  @override
  String get freezeUsed => 'Заморозка серии использована';

  @override
  String get guestLogoutTitle => 'Выйти из гостевого режима?';

  @override
  String get guestLogoutBody =>
      'Прогресс не привязан к аккаунту и будет потерян.';

  @override
  String get history => 'История';

  @override
  String get kindDailyQuestion => 'Вопрос дня';

  @override
  String get kindLeagueEnding => 'Лига заканчивается';

  @override
  String get kindStreakReminder => 'Напоминание о серии';

  @override
  String get listen => 'Слушать';

  @override
  String get maxPerDay => 'Максимум в день';

  @override
  String get mergeFailed =>
      'Вход выполнен, но гостевой прогресс не удалось объединить';

  @override
  String get noReviewDue => 'Сейчас нечего повторять';

  @override
  String get notAnswered => 'Нет ответа';

  @override
  String get notificationSettings => 'Уведомления';

  @override
  String get pauseAudio => 'Пауза';

  @override
  String get playAudio => 'Воспроизвести';

  @override
  String get quietHours => 'Тихие часы';

  @override
  String get reportQuestion => 'Сообщить об ошибке';

  @override
  String get reportReason => 'Что не так с этим вопросом?';

  @override
  String get reportSent => 'Спасибо, жалоба отправлена';

  @override
  String get reviewAnswers => 'Разбор ответов';

  @override
  String get save => 'Сохранить';

  @override
  String get saveProgress => 'Сохраните прогресс';

  @override
  String get saveProgressBody =>
      'Войдите или создайте аккаунт, чтобы не потерять серию и XP.';

  @override
  String get saved => 'Сохранено';

  @override
  String get send => 'Отправить';

  @override
  String get sessionExpired => 'Сессия истекла. Войдите снова.';

  @override
  String get streakAtRisk => 'Серия под угрозой — позанимайтесь сегодня!';

  @override
  String get tabFriends => 'Друзья';

  @override
  String get tabLeague => 'Лига';

  @override
  String get tabLyceum => 'Лицей';

  @override
  String get useFreeze => 'Применить заморозку';

  @override
  String get weekly => 'Неделя';

  @override
  String get yourAnswer => 'Ваш ответ';

  @override
  String minutesShort(int n) {
    return '$n мин';
  }

  @override
  String durationDaysHours(int days, int hours) {
    return '$daysд $hoursч';
  }

  @override
  String durationHoursMinutes(int hours, int minutes) {
    return '$hoursч $minutesм';
  }

  @override
  String streakFreezes(int n) {
    return 'Заморозок серии: $n';
  }

  @override
  String get chooseCity => 'Город';

  @override
  String get cityHint =>
      'Или город, в котором вы планируете учиться. Не выбирайте, если готовы учиться в разных городах.';

  @override
  String get anyCity => 'Любой город';

  @override
  String get chooseSubjects => 'Предметы (один или несколько)';

  @override
  String get dormitory => 'Общежитие';

  @override
  String get dormitoryAvailable => 'Есть общежитие';

  @override
  String get dormitoryLimited => 'Места в общежитии ограничены';

  @override
  String get dormitoryNone => 'Общежития нет';

  @override
  String get dormitoryUnknown => 'Нет данных об общежитии';

  @override
  String get dreamLyceums => 'Мои лицеи мечты';

  @override
  String get dreamRules =>
      'Можно выбрать до 3 лицеев по приоритету. Ваш балл сначала сравнивается с 1-м выбором. Если его хватает, вы зачислены туда, а 2-й и 3-й не рассматриваются. Если нет, проверяется 2-й выбор, затем 3-й. Если не подходит ни один, результат показывается по 1-му выбору. Поставьте настоящую мечту первой, а более надёжный вариант — третьим.';

  @override
  String get moveUp => 'Выше';

  @override
  String get moveDown => 'Ниже';

  @override
  String get removeItem => 'Убрать';

  @override
  String get emptySlot => 'Свободное место';

  @override
  String get addToDreams => 'Добавить в мечты';

  @override
  String get removeFromDreams => 'Убрать из мечт';

  @override
  String get addLyceum => 'Добавить лицей';

  @override
  String get tooManyDreams => 'Можно выбрать не более 3 лицеев.';
}
