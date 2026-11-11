import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models.dart';
import 'api_client.dart';
import 'token_storage.dart';

/// Typed access to the endpoints in apps/api/openapi/openapi.json.
class Api {
  Api(this._d);
  final Dio _d;

  Future<T> _get<T>(String path, [Map<String, dynamic>? q]) async =>
      (await _d.get<T>(path, queryParameters: q)).data as T;
  Future<T> _post<T>(String path, [Object? body]) async =>
      (await _d.post<T>(path, data: body)).data as T;
  Future<T> _put<T>(String path, [Object? body]) async =>
      (await _d.put<T>(path, data: body)).data as T;

  Future<List<Json>> _getList(String path, [Map<String, dynamic>? q]) async =>
      ((await _get<List<dynamic>>(path, q))).cast<Json>();

  // ---- identity ----
  Future<void> register({required String email, required String name, required String password, required String locale}) =>
      _post<dynamic>('/v1/identity/register', {'email': email, 'name': name, 'password': password, 'locale': locale});

  Future<TokenPair> verifyEmail(String email, String code) async =>
      _tokens(await _post<Json>('/v1/identity/email/verify', {'email': email, 'code': code}));

  Future<void> resendCode(String email) => _post<dynamic>('/v1/identity/email/resend', {'email': email});

  Future<void> forgotPassword(String email) => _post<dynamic>('/v1/identity/password/forgot', {'email': email});

  Future<TokenPair> resetPassword(String email, String code, String password) async =>
      _tokens(await _post<Json>('/v1/identity/password/reset', {'email': email, 'code': code, 'password': password}));

  Future<TokenPair> login(String email, String password) async =>
      _tokens(await _post<Json>('/v1/identity/login', {'email': email, 'password': password}));

  Future<void> logout(String refreshToken) => _post<dynamic>('/v1/identity/logout', {'refresh_token': refreshToken});

  Future<Me> me() async => Me.fromJson(await _get<Json>('/v1/identity/me'));

  Future<Me> patchMe({String? name, String? locale, String? targetLyceumId, String? educationLanguageId}) async =>
      Me.fromJson((await _d.patch<Json>('/v1/identity/me', data: {
        if (name != null) 'name': name,
        if (locale != null) 'locale': locale,
        if (targetLyceumId != null) 'target_lyceum_id': targetLyceumId,
        if (educationLanguageId != null) 'education_language_id': educationLanguageId,
      }))
          .data!);

  Future<void> registerDevice(String platform, String token) =>
      _post<dynamic>('/v1/notify/devices', {'platform': platform, 'token': token});

  /// Anonymous account for first launch (`POST /v1/identity/guest`).
  Future<TokenPair> guest() async => _tokens(await _post<Json>('/v1/identity/guest', <String, dynamic>{}));

  /// Moves a guest's progress into the account the client is now authenticated as.
  Future<void> mergeGuest(String guestAccessToken) =>
      _post<dynamic>('/v1/learning/merge-guest', {'guest_access_token': guestAccessToken});

  Future<void> setDailyGoal(int xp) => _put<dynamic>('/v1/me/daily-goal', {'xp': xp});

  Future<Passage> passage(String id) async => Passage.fromJson(await _get<Json>('/v1/bank/passages/$id'));

  TokenPair _tokens(Json j) => TokenPair(j['access_token'] as String, j['refresh_token'] as String);

  // ---- catalog ----
  Future<List<Subject>> subjects() async => (await _getList('/v1/catalog/subjects')).map(Subject.fromJson).toList();

  /// Returns null when the subject has no published path (404).
  Future<LearnerPath?> path(String subjectId, String language, String locale) async {
    try {
      return LearnerPath.fromJson(
          await _get<Json>('/v1/catalog/subjects/$subjectId/path', {'language': language, 'locale': locale}));
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }

  // ---- learning ----
  Future<SessionData> startLesson(String lessonId, String language) async =>
      SessionData.fromJson(await _post<Json>('/v1/learning/lessons/start', {'lesson_id': lessonId, 'language': language}));

  Future<SessionData> startDrill(String subjectId, String language, {String? topicId, String? typeId, int count = 10}) async =>
      SessionData.fromJson(await _post<Json>('/v1/learning/drills/start', {
        'subject_id': subjectId,
        'language': language,
        'count': count,
        if (topicId != null) 'topic_id': topicId,
        if (typeId != null) 'type_id': typeId,
      }));

  Future<SessionData> startReview(String subjectId, String language) async =>
      SessionData.fromJson(await _post<Json>('/v1/learning/review/start', {'subject_id': subjectId, 'language': language}));

  Future<SessionData> startPlacement(String subjectId, String language) async =>
      SessionData.fromJson(await _post<Json>('/v1/learning/placement/start', {'subject_id': subjectId, 'language': language}));

  Future<Placement?> placement(String subjectId) async {
    final j = (await _d.get<Json?>('/v1/learning/placement/$subjectId')).data;
    return j == null ? null : Placement.fromJson(j);
  }

  Future<Placement> skipPlacement(String subjectId) async =>
      Placement.fromJson(await _post<Json>('/v1/learning/placement/$subjectId/skip'));

  Future<int> reviewDue(String subjectId) async =>
      ((await _get<Json>('/v1/learning/review/summary', {'subject_id': subjectId}))['due'] as num?)?.toInt() ?? 0;

  Future<List<WeakArea>> weakAreas(String subjectId) async =>
      (await _getList('/v1/learning/weak-areas/$subjectId', {'limit': 5})).map(WeakArea.fromJson).toList();

  Future<AnswerResult> answer(String sessionId, String questionId, Json response, int timeMs) async =>
      AnswerResult.fromJson(await _post<Json>('/v1/learning/sessions/$sessionId/answers',
          {'question_id': questionId, 'response': response, 'time_ms': timeMs}));

  Future<FinishResult> finishSession(String sessionId) async =>
      FinishResult.fromJson(await _post<Json>('/v1/learning/sessions/$sessionId/finish'));

  // ---- assessment ----
  Future<List<Mock>> mocks() async => (await _getList('/v1/assessment/mocks')).map(Mock.fromJson).toList();

  Future<Attempt> startAttempt(String blueprintId, String language) async =>
      Attempt.fromJson(await _post<Json>('/v1/assessment/attempts', {'blueprint_id': blueprintId, 'language': language}));

  Future<Attempt> startPersonalAttempt(String subjectId, String language) async =>
      Attempt.fromJson(await _post<Json>('/v1/assessment/attempts/personal', {'subject_id': subjectId, 'language': language}));

  Future<Attempt?> activeAttempt() async {
    final j = (await _d.get<Json?>('/v1/assessment/attempts/active')).data;
    return j == null ? null : Attempt.fromJson(j);
  }

  Future<Attempt> saveAttempt(String id, Json answers, List<String> flags) async =>
      Attempt.fromJson((await _d.patch<Json>('/v1/assessment/attempts/$id', data: {'answers': answers, 'flags': flags})).data!);

  Future<AttemptResult> submitAttempt(String id) async =>
      AttemptResult.fromJson(await _post<Json>('/v1/assessment/attempts/$id/submit'));

  Future<AttemptResult> attemptResult(String id) async =>
      AttemptResult.fromJson(await _get<Json>('/v1/assessment/attempts/$id/result'));

  Future<List<HistoryItem>> history() async =>
      (await _getList('/v1/assessment/attempts/history', {'limit': 20})).map(HistoryItem.fromJson).toList();

  Future<Prediction?> prediction() async => predictionFromJson(await _get<Json>('/v1/assessment/prediction'));

  // ---- gamification ----
  Future<Stats> stats() async => Stats.fromJson(await _get<Json>('/v1/me/stats'));

  Future<List<Quest>> quests() async => (await _getList('/v1/gamification/quests')).map(Quest.fromJson).toList();

  Future<League?> league() async {
    final j = (await _d.get<Json?>('/v1/gamification/leagues/current')).data;
    return j == null ? null : League.fromJson(j);
  }

  Future<Stats> useStreakFreeze() async => Stats.fromJson(await _post<Json>('/v1/gamification/streak/freeze'));

  /// [period] is `week` or `all`.
  Future<Board> friendsBoard(String period) async =>
      Board.fromJson(await _get<Json>('/v1/gamification/leaderboard/friends', {'period': period}));

  Future<Board> lyceumBoard(String period) async =>
      Board.fromJson(await _get<Json>('/v1/gamification/leaderboard/lyceum', {'period': period, 'limit': 50}));

  Future<NotifyPrefs> notifyPrefs() async => NotifyPrefs.fromJson(await _get<Json>('/v1/notify/preferences'));

  Future<NotifyPrefs> saveNotifyPrefs(NotifyPrefs p) async =>
      NotifyPrefs.fromJson(await _put<Json>('/v1/notify/preferences', p.toJson()));

  Future<SessionData> session(String id) async => SessionData.fromJson(await _get<Json>('/v1/learning/sessions/$id'));

  /// Premium / quota-limited; throws a DioException with a problem body when not allowed.
  Future<String> explain(String questionId, String locale) async =>
      ((await _post<Json>('/v1/ai/explain/$questionId', {'locale': locale}))['explanation'] as String?) ?? '';

  /// Returns true when the question was hidden by the report.
  Future<bool> reportQuestion(String questionId, String reason) async =>
      (await _post<Json>('/v1/bank/questions/$questionId/report', {'reason': reason}))['hidden'] as bool? ?? false;

  Future<List<Friend>> friends() async => (await _getList('/v1/gamification/friends')).map(Friend.fromJson).toList();

  // ---- lyceums (public) ----
  Future<List<Lyceum>> lyceums({String? q}) async =>
      (await _getList('/v1/lyceums', {'limit': 100, if (q != null && q.isNotEmpty) 'q': q})).map(Lyceum.fromJson).toList();

  Future<LyceumDetail> lyceum(String id) async => LyceumDetail.fromJson(await _get<Json>('/v1/lyceums/$id'));

  Future<List<EduLanguage>> languages() async =>
      (await _getList('/v1/lyceums/languages')).map(EduLanguage.fromJson).toList();

  // ---- billing (read only) ----
  Future<Billing> billing() async => Billing.fromJson(await _get<Json>('/v1/billing/me'));

  Future<List<Plan>> plans() async => (await _getList('/v1/billing/plans')).map(Plan.fromJson).toList();
}

final apiProvider = Provider<Api>((ref) => Api(ref.watch(dioProvider)));
