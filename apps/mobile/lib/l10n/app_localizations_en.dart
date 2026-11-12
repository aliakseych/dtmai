// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'DTM AI';

  @override
  String get continueLabel => 'Continue';

  @override
  String get check => 'Check';

  @override
  String get skip => 'Skip';

  @override
  String get correct => 'Correct!';

  @override
  String get incorrect => 'Incorrect';

  @override
  String get correctAnswer => 'Correct answer:';

  @override
  String get explanation => 'Explanation';

  @override
  String get signIn => 'Sign in';

  @override
  String get email => 'Email';

  @override
  String get sendCode => 'Send code';

  @override
  String get code => 'Verification code';

  @override
  String get verify => 'Verify';

  @override
  String get orLabel => 'or';

  @override
  String get onboardingTitle => 'Choose your goal';

  @override
  String get chooseLyceum => 'Lyceum';

  @override
  String get chooseLanguage => 'Education language';

  @override
  String get startPlacement => 'Start placement test';

  @override
  String get learn => 'Learn';

  @override
  String get practice => 'Practice';

  @override
  String get mocks => 'Mock exams';

  @override
  String get leagues => 'Leagues';

  @override
  String get quests => 'Quests';

  @override
  String get profile => 'Profile';

  @override
  String get premium => 'Premium';

  @override
  String get lyceums => 'Lyceums';

  @override
  String get hearts => 'Hearts';

  @override
  String get noHearts => 'Out of hearts. Come back later or go Premium.';

  @override
  String streakDays(int n) {
    return '$n day streak';
  }

  @override
  String get gems => 'Gems';

  @override
  String get xp => 'XP';

  @override
  String get dailyGoal => 'Daily goal';

  @override
  String get mistakes => 'Review mistakes';

  @override
  String get weakTopics => 'Weak topics';

  @override
  String get bankDrill => 'Question bank';

  @override
  String get personalMock => 'Personal mock';

  @override
  String get start => 'Start';

  @override
  String get submit => 'Submit';

  @override
  String get finish => 'Finish';

  @override
  String get timeLeft => 'Time left';

  @override
  String get markReview => 'Mark for review';

  @override
  String get navigator => 'Question map';

  @override
  String answeredCount(int a, int t) {
    return '$a of $t answered';
  }

  @override
  String get score => 'Score';

  @override
  String get predictedScore => 'Predicted score';

  @override
  String get lessonComplete => 'Lesson complete!';

  @override
  String get dailyQuests => 'Daily quests';

  @override
  String get weeklyLeague => 'Weekly league';

  @override
  String get rank => 'Rank';

  @override
  String get friends => 'Friends';

  @override
  String get logout => 'Log out';

  @override
  String get language => 'Language';

  @override
  String get retry => 'Retry';

  @override
  String get errorGeneric => 'Something went wrong';

  @override
  String get empty => 'Nothing here yet';

  @override
  String get typeAnswer => 'Type your answer';

  @override
  String get premiumPerks =>
      'AI explanations, AI tutor, personal mocks and analytics';

  @override
  String get quota => 'Quota';

  @override
  String get applications => 'Applications';

  @override
  String get competition => 'Competition';

  @override
  String get year => 'Year';

  @override
  String get search => 'Search';

  @override
  String get previousYears => 'Previous years';

  @override
  String get streakReminderTitle => 'Keep your streak alive!';

  @override
  String get streakReminderBody =>
      'Do today’s lesson — Temur is waiting for you.';

  @override
  String get reminderChannel => 'Reminders';

  @override
  String get password => 'Password';

  @override
  String get nameLabel => 'Name';

  @override
  String get signUp => 'Sign up';

  @override
  String get haveAccount => 'Already have an account? Sign in';

  @override
  String get noAccount => 'No account yet? Sign up';

  @override
  String get notNow => 'Not now';

  @override
  String get resendCode => 'Resend code';

  @override
  String get verifyPrompt => 'Enter the code we emailed you';

  @override
  String get guestGateMessage => 'Create an account to use this feature';

  @override
  String get skipPlacement => 'Skip placement test';

  @override
  String get placementBannerTitle => 'Take the placement test';

  @override
  String get placementBannerBody => 'We will tailor your path to your level';

  @override
  String get noPath => 'No path for this subject yet';

  @override
  String get noFriends => 'No friends yet';

  @override
  String get streakLabel => 'Streak';

  @override
  String get planPremium => 'Premium active';

  @override
  String get planFree => 'Free plan';

  @override
  String get reviewToEarn => 'Review your mistakes to earn hearts';

  @override
  String get waitForRefill => 'Or wait for hearts to refill';

  @override
  String get heartsBanner => 'You are out of hearts';

  @override
  String get exitConfirmTitle => 'Leave the lesson?';

  @override
  String get exitConfirmBody => 'Your progress in this lesson will be lost.';

  @override
  String get cancel => 'Cancel';

  @override
  String get leave => 'Leave';

  @override
  String get placementDone => 'Placement complete! Your path is ready.';

  @override
  String get accuracy => 'Accuracy';

  @override
  String get resumeAttempt => 'Resume your exam';

  @override
  String get submitConfirmTitle => 'Submit the exam?';

  @override
  String get exitMockTitle => 'Leave the exam?';

  @override
  String get exitMockBody =>
      'Your answers are saved; you can resume later while time remains.';

  @override
  String get autosaveFailed => 'Could not save your answers';

  @override
  String get onTrack => 'On track for the passing score';

  @override
  String get offTrack => 'Below the passing score';

  @override
  String get passingScore => 'Passing score';

  @override
  String get gap => 'Gap';

  @override
  String get setTarget => 'Set as my target';

  @override
  String get premiumWebOnly => 'Subscriptions are managed on our website';

  @override
  String get monthsShort => 'mo.';

  @override
  String get chooseSubject => 'Subject';

  @override
  String planActive(String date) {
    return 'Premium until $date';
  }

  @override
  String refillIn(String time) {
    return 'Next heart in $time';
  }

  @override
  String leagueEndsIn(String time) {
    return 'Ends in $time';
  }

  @override
  String submitConfirmBody(int unanswered, int flagged) {
    return '$unanswered unanswered, $flagged flagged. Submit anyway?';
  }

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get resetPassword => 'Reset password';

  @override
  String get newPassword => 'New password';

  @override
  String get resetPrompt => 'Enter the code from the email and a new password';

  @override
  String get invalidCode => 'Invalid or expired code';

  @override
  String get weakPassword => 'Password is too weak';

  @override
  String get allTime => 'All time';

  @override
  String get answersNotAccepted =>
      'Time is up – your last answers were not accepted. Submitting now.';

  @override
  String get audioFailed => 'Could not play audio';

  @override
  String get channelEmail => 'Email';

  @override
  String get channelPush => 'Push';

  @override
  String get channelTelegram => 'Telegram';

  @override
  String get drillWeakTopics => 'Practice weak topics';

  @override
  String get explain => 'Explain';

  @override
  String get freezeUsed => 'Streak freeze used';

  @override
  String get guestLogoutTitle => 'Log out as guest?';

  @override
  String get guestLogoutBody =>
      'Your progress is not saved to an account and will be lost.';

  @override
  String get history => 'History';

  @override
  String get kindDailyQuestion => 'Daily question';

  @override
  String get kindLeagueEnding => 'League ending';

  @override
  String get kindStreakReminder => 'Streak reminder';

  @override
  String get listen => 'Listen';

  @override
  String get maxPerDay => 'Max per day';

  @override
  String get mergeFailed => 'Signed in, but guest progress could not be merged';

  @override
  String get noReviewDue => 'Nothing to review right now';

  @override
  String get notAnswered => 'Not answered';

  @override
  String get notificationSettings => 'Notifications';

  @override
  String get pauseAudio => 'Pause';

  @override
  String get playAudio => 'Play';

  @override
  String get quietHours => 'Quiet hours';

  @override
  String get reportQuestion => 'Report a problem';

  @override
  String get reportReason => 'What is wrong with this question?';

  @override
  String get reportSent => 'Thanks, report sent';

  @override
  String get reviewAnswers => 'Review answers';

  @override
  String get save => 'Save';

  @override
  String get saveProgress => 'Save your progress';

  @override
  String get saveProgressBody =>
      'Sign in or create an account so you never lose your streak and XP.';

  @override
  String get saved => 'Saved';

  @override
  String get send => 'Send';

  @override
  String get sessionExpired =>
      'Your session has expired. Please sign in again.';

  @override
  String get streakAtRisk => 'Your streak is at risk – practice today!';

  @override
  String get tabFriends => 'Friends';

  @override
  String get tabLeague => 'League';

  @override
  String get tabLyceum => 'Lyceum';

  @override
  String get useFreeze => 'Use freeze';

  @override
  String get weekly => 'This week';

  @override
  String get yourAnswer => 'Your answer';

  @override
  String minutesShort(int n) {
    return '$n min';
  }

  @override
  String durationDaysHours(int days, int hours) {
    return '${days}d ${hours}h';
  }

  @override
  String durationHoursMinutes(int hours, int minutes) {
    return '${hours}h ${minutes}m';
  }

  @override
  String streakFreezes(int n) {
    return 'Streak freezes: $n';
  }

  @override
  String get chooseCity => 'City';

  @override
  String get cityHint =>
      'Or the city where you plan to study. Don\'t pick one if you\'re open to studying in different cities.';

  @override
  String get anyCity => 'Any city';

  @override
  String get chooseSubjects => 'Subjects (pick one or more)';

  @override
  String get dormitory => 'Dormitory';

  @override
  String get dormitoryAvailable => 'Dormitory available';

  @override
  String get dormitoryLimited => 'Limited dormitory places';

  @override
  String get dormitoryNone => 'No dormitory';

  @override
  String get dormitoryUnknown => 'Dormitory info unknown';

  @override
  String get dreamLyceums => 'My dream lyceums';

  @override
  String get dreamRules =>
      'You can choose up to 3 lyceums in order of priority. Your score is checked against your 1st choice first. If it\'s enough, you\'re admitted there and the 2nd and 3rd aren\'t considered. If not, your 2nd choice is checked, then the 3rd. If none fits, your result is shown under your 1st choice. Put your real dream first and a safer option third.';

  @override
  String get moveUp => 'Move up';

  @override
  String get moveDown => 'Move down';

  @override
  String get removeItem => 'Remove';

  @override
  String get emptySlot => 'Empty slot';

  @override
  String get addToDreams => 'Add to my dreams';

  @override
  String get removeFromDreams => 'Remove from my dreams';

  @override
  String get addLyceum => 'Add a lyceum';

  @override
  String get tooManyDreams => 'You can pick up to 3 lyceums.';
}
