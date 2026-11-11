// Hand-written models. Field names follow apps/api/openapi/openapi.json (snake_case).

typedef Json = Map<String, dynamic>;

List<Json> _list(Object? v) => (v as List? ?? const []).cast<Json>();
Json _json(Object? v) => (v as Map?)?.cast<String, dynamic>() ?? <String, dynamic>{};
Json? _jsonOpt(Object? v) => v == null ? null : _json(v);
Map<String, String> _names(Object? v) =>
    {for (final e in ((v as Map?) ?? const {}).entries) e.key.toString(): '${e.value}'};
List<String> _strs(Object? v) => ((v as List?) ?? const []).map((e) => '$e').toList();
double _num(Object? v) => (v as num?)?.toDouble() ?? 0;
int _int(Object? v) => (v as num?)?.toInt() ?? 0;

/// Picks a localized name from a `{locale: text}` map.
String pickName(Map<String, String> names, String tag) {
  final lang = tag.split('-').first;
  for (final k in [tag, lang, 'uz-Latn', 'uz', 'en']) {
    final v = names[k];
    if (v != null && v.isNotEmpty) return v;
  }
  return names.values.isEmpty ? '' : names.values.first;
}

class Me {
  const Me({
    required this.id,
    required this.name,
    this.email,
    this.emailVerified = false,
    this.locale = 'uz-Latn',
    this.targetLyceumId,
    this.educationLanguageId,
  });
  factory Me.fromJson(Json j) => Me(
        id: j['id'] as String,
        name: (j['name'] as String?) ?? '',
        email: j['email'] as String?,
        emailVerified: j['email_verified'] as bool? ?? false,
        locale: (j['locale'] as String?) ?? 'uz-Latn',
        targetLyceumId: j['target_lyceum_id'] as String?,
        educationLanguageId: j['education_language_id'] as String?,
      );
  final String id;
  final String name;
  final String? email;
  final bool emailVerified;
  final String locale;
  final String? targetLyceumId;
  final String? educationLanguageId;
}

class Hearts {
  const Hearts({required this.count, required this.max, this.nextRefillAt, this.unlimited = false});
  factory Hearts.fromJson(Json j) => Hearts(
        count: _int(j['count']),
        max: _int(j['max']),
        nextRefillAt: DateTime.tryParse('${j['next_refill_at'] ?? ''}')?.toLocal(),
        unlimited: j['unlimited'] as bool? ?? false,
      );
  final int count;
  final int max;
  final DateTime? nextRefillAt;
  final bool unlimited;
  bool get empty => !unlimited && count <= 0;
}

class LeagueTier {
  const LeagueTier({required this.code, required this.name, required this.idx});
  factory LeagueTier.fromJson(Json j) =>
      LeagueTier(code: '${j['code']}', name: _names(j['name']), idx: _int(j['idx']));
  final String code;
  final Map<String, String> name;
  final int idx;
}

/// `GET /v1/me/stats`.
class Stats {
  const Stats({
    required this.gems,
    required this.hearts,
    required this.streak,
    required this.streakLongest,
    required this.streakActiveToday,
    required this.streakAtRisk,
    required this.xpToday,
    this.dailyGoalXp = 50,
    this.todayXp = 0,
    required this.xpTotal,
    required this.lessonsCompleted,
    this.streakFreezes = 0,
    this.leagueTier,
  });
  factory Stats.fromJson(Json j) => Stats(
        gems: _int(j['gems']),
        hearts: Hearts.fromJson(_json(j['hearts'])),
        streak: _int(j['streak']),
        streakLongest: _int(j['streak_longest']),
        streakActiveToday: j['streak_active_today'] as bool? ?? false,
        streakAtRisk: j['streak_at_risk'] as bool? ?? false,
        xpToday: _int(j['xp_today']),
        dailyGoalXp: j['daily_goal_xp'] == null ? 50 : _int(j['daily_goal_xp']),
        todayXp: j['today_xp'] == null ? _int(j['xp_today']) : _int(j['today_xp']),
        xpTotal: _int(j['xp_total']),
        lessonsCompleted: _int(j['lessons_completed']),
        streakFreezes: _int(j['streak_freezes']),
        leagueTier: _jsonOpt(j['league_tier']) == null ? null : LeagueTier.fromJson(_json(j['league_tier'])),
      );
  final int gems;
  final Hearts hearts;
  final int streak;
  final int streakLongest;
  final bool streakActiveToday;
  final bool streakAtRisk;
  final int xpToday;
  final int dailyGoalXp;
  final int todayXp;
  final int xpTotal;
  final int lessonsCompleted;
  final int streakFreezes;
  final LeagueTier? leagueTier;
}

class Subject {
  const Subject({required this.id, required this.code, required this.names});
  factory Subject.fromJson(Json j) =>
      Subject(id: j['id'] as String, code: '${j['code']}', names: _names(j['names']));
  final String id;
  final String code;
  final Map<String, String> names;
}

/// `progress` on path units and lessons; `state` is `locked|open|done`.
class PathProgress {
  const PathProgress({this.completedLessons = 0, this.totalLessons = 0, this.state = 'open'});
  factory PathProgress.fromJson(Object? v) {
    final j = _json(v);
    return PathProgress(
      completedLessons: _int(j['completed_lessons']),
      totalLessons: _int(j['total_lessons']),
      state: (j['state'] as String?) ?? 'open',
    );
  }
  final int completedLessons;
  final int totalLessons;
  final String state;
  bool get locked => state == 'locked';
  bool get done => state == 'done';
}

class PathLesson {
  const PathLesson({
    required this.id,
    required this.title,
    required this.questionCount,
    required this.legendary,
    this.progress = const PathProgress(),
  });
  factory PathLesson.fromJson(Json j) => PathLesson(
        id: j['id'] as String,
        title: (j['title'] as String?) ?? '',
        questionCount: _int(j['question_count']),
        legendary: j['legendary'] as bool? ?? false,
        progress: PathProgress.fromJson(j['progress']),
      );
  final String id;
  final String title;
  final int questionCount;
  final bool legendary;
  final PathProgress progress;
}

class PathUnit {
  const PathUnit({required this.id, required this.title, required this.lessons, this.progress = const PathProgress()});
  factory PathUnit.fromJson(Json j) => PathUnit(
        id: j['id'] as String,
        title: (j['title'] as String?) ?? '',
        lessons: _list(j['lessons']).map(PathLesson.fromJson).toList(),
        progress: PathProgress.fromJson(j['progress']),
      );
  final String id;
  final String title;
  final List<PathLesson> lessons;
  final PathProgress progress;
}

class LearnerPath {
  const LearnerPath({required this.id, required this.units});
  factory LearnerPath.fromJson(Json j) =>
      LearnerPath(id: j['id'] as String, units: _list(j['units']).map(PathUnit.fromJson).toList());
  final String id;
  final List<PathUnit> units;
}

class Placement {
  const Placement({required this.skipped, required this.startUnitIndex, this.ability});
  factory Placement.fromJson(Json j) => Placement(
        skipped: j['skipped'] as bool? ?? false,
        startUnitIndex: _int(j['start_unit_index']),
        ability: (j['ability'] as num?)?.toDouble(),
      );
  final bool skipped;
  final int startUnitIndex;
  final double? ability;
}

class WeakArea {
  const WeakArea({required this.topicId, required this.typeId, required this.score, required this.attempts, this.topicName});
  factory WeakArea.fromJson(Json j) => WeakArea(
        topicId: j['topic_id'] as String?,
        typeId: j['type_id'] as String?,
        score: _num(j['score']),
        attempts: _int(j['attempts']),
        topicName: j['topic_name'] as String?,
      );
  final String? topicId;
  final String? typeId;
  final double score;
  final int attempts;
  final String? topicName;
}

/// A question shown to the learner (`ItemOut` / `AttemptItemOut`).
class Item {
  const Item({
    required this.id,
    required this.kind,
    required this.stem,
    required this.payload,
    this.media = const [],
    this.passageId,
    this.topicId,
    this.typeId,
    this.section,
    this.children = const [],
  });
  factory Item.fromJson(Json j) => Item(
        id: j['id'] as String,
        kind: '${j['kind']}',
        stem: (j['stem'] as String?) ?? '',
        payload: _json(j['payload']),
        media: _list(j['media']).map(MediaRef.fromJson).toList(),
        passageId: j['passage_id'] as String?,
        topicId: j['topic_id'] as String?,
        typeId: j['type_id'] as String?,
        section: j['section'] as int?,
        children: _list(j['children']).map(Item.fromJson).toList(),
      );
  final String id;
  final String kind;
  final String stem;
  final Json payload;
  final List<MediaRef> media;
  final String? passageId;
  final String? topicId;
  final String? typeId;
  final int? section;

  /// Sub-questions of a `passage_group` (answered as one `{answers: {childId: response}}`).
  final List<Item> children;

  /// URL of the first image media, if any.
  String? get imageUrl => _firstUrl('image');

  /// URL of the first audio media, if any.
  String? get audioUrl => _firstUrl('audio');

  String? _firstUrl(String kind) {
    for (final m in media) {
      if (m.kind == kind && m.url.isNotEmpty) return m.url;
    }
    return null;
  }

  /// `payload.options` / `left` / `right` / `items` as `{id, text}` rows.
  List<ChoiceOpt> optionsOf(String key) => _list(payload[key]).map(ChoiceOpt.fromJson).toList();
}

/// `{kind: image|audio, url, alt?}`.
class MediaRef {
  const MediaRef({required this.kind, required this.url, this.alt});
  factory MediaRef.fromJson(Json j) => MediaRef(kind: '${j['kind']}', url: '${j['url'] ?? ''}', alt: j['alt'] as String?);
  final String kind;
  final String url;
  final String? alt;
}

/// `GET /v1/bank/passages/{id}`.
class Passage {
  const Passage({required this.id, required this.text, this.media = const []});
  factory Passage.fromJson(Json j) => Passage(
        id: '${j['id']}',
        text: (j['text'] as String?) ?? '',
        media: _list(j['media']).map(MediaRef.fromJson).toList(),
      );
  final String id;
  final String text;
  final List<MediaRef> media;
}

class ChoiceOpt {
  const ChoiceOpt({required this.id, required this.text});
  factory ChoiceOpt.fromJson(Json j) => ChoiceOpt(id: '${j['id']}', text: '${j['text'] ?? ''}');
  final String id;
  final String text;
}

class SessionData {
  const SessionData({
    required this.id,
    required this.mode,
    required this.subjectId,
    required this.items,
    required this.answered,
    required this.correct,
    required this.total,
    required this.hearts,
    required this.unlimitedHearts,
  });
  factory SessionData.fromJson(Json j) => SessionData(
        id: j['id'] as String,
        mode: '${j['mode']}',
        subjectId: j['subject_id'] as String?,
        items: _list(j['items']).map(Item.fromJson).toList(),
        answered: _int(j['answered']),
        correct: _int(j['correct']),
        total: _int(j['total']),
        hearts: j['hearts'] as int?,
        unlimitedHearts: j['unlimited_hearts'] as bool? ?? false,
      );
  final String id;
  final String mode;
  final String? subjectId;
  final List<Item> items;
  final int answered;
  final int correct;
  final int total;
  final int? hearts;
  final bool unlimitedHearts;
}

class AnswerResult {
  const AnswerResult({
    required this.correct,
    required this.correctResponse,
    required this.sessionDone,
    required this.answered,
    required this.total,
    required this.unlimitedHearts,
    this.hearts,
    this.nextItem,
  });
  factory AnswerResult.fromJson(Json j) => AnswerResult(
        correct: j['correct'] as bool? ?? false,
        correctResponse: _json(j['correct_response']),
        sessionDone: j['session_done'] as bool? ?? false,
        answered: _int(j['answered']),
        total: _int(j['total']),
        unlimitedHearts: j['unlimited_hearts'] as bool? ?? false,
        hearts: j['hearts'] as int?,
        nextItem: _jsonOpt(j['next_item']) == null ? null : Item.fromJson(_json(j['next_item'])),
      );
  final bool correct;
  final Json correctResponse;
  final bool sessionDone;
  final int answered;
  final int total;
  final bool unlimitedHearts;
  final int? hearts;
  final Item? nextItem;
}

class FinishResult {
  const FinishResult({
    required this.mode,
    required this.answered,
    required this.correct,
    required this.total,
    required this.xpBase,
    this.startUnitIndex,
  });
  factory FinishResult.fromJson(Json j) => FinishResult(
        mode: '${j['mode']}',
        answered: _int(j['answered']),
        correct: _int(j['correct']),
        total: _int(j['total']),
        xpBase: _int(j['xp_base']),
        startUnitIndex: j['start_unit_index'] as int?,
      );
  final String mode;
  final int answered;
  final int correct;
  final int total;
  final int xpBase;
  final int? startUnitIndex;
}

class Mock {
  const Mock({required this.id, required this.names, required this.durationMin, required this.questionCount, required this.kind});
  factory Mock.fromJson(Json j) => Mock(
        id: j['id'] as String,
        names: _names(j['names']),
        durationMin: _int(j['duration_min']),
        questionCount: _int(j['question_count']),
        kind: '${j['kind']}',
      );
  final String id;
  final Map<String, String> names;
  final int durationMin;
  final int questionCount;
  final String kind;
}

class Attempt {
  const Attempt({
    required this.id,
    required this.items,
    required this.answers,
    required this.flags,
    required this.timeLeftS,
    required this.status,
    required this.kind,
    required this.deadline,
    required this.serverNow,
    this.accepted = true,
  });
  factory Attempt.fromJson(Json j) => Attempt(
        id: j['id'] as String,
        items: _list(j['items']).map(Item.fromJson).toList(),
        answers: _json(j['answers']),
        flags: _strs(j['flags']),
        timeLeftS: _int(j['time_left_s']),
        status: '${j['status']}',
        kind: '${j['kind']}',
        deadline: DateTime.tryParse('${j['deadline'] ?? ''}'),
        serverNow: DateTime.tryParse('${j['server_now'] ?? ''}'),
        accepted: j['accepted'] as bool? ?? true,
      );
  final String id;
  final List<Item> items;
  final Json answers;
  final List<String> flags;
  final int timeLeftS;
  final String status;
  final String kind;

  /// Server-side exam deadline and the server clock at response time (the timer source of truth).
  final DateTime? deadline;
  final DateTime? serverNow;

  /// False when the server rejected a save (deadline passed).
  final bool accepted;
}

class ReviewRow {
  const ReviewRow({required this.questionId, required this.correct, required this.answered, required this.correctResponse, required this.response});
  factory ReviewRow.fromJson(Json j) => ReviewRow(
        questionId: '${j['question_id']}',
        correct: j['correct'] as bool? ?? false,
        answered: j['answered'] as bool? ?? false,
        correctResponse: _json(j['correct_response']),
        response: _jsonOpt(j['response']),
      );
  final String questionId;
  final bool correct;
  final bool answered;
  final Json correctResponse;
  final Json? response;
}

class Comparison {
  const Comparison({required this.passingScore, required this.gap, required this.onTrack, this.year, this.competitionRatio});
  factory Comparison.fromJson(Json j) => Comparison(
        passingScore: _num(j['passing_score']),
        gap: _num(j['gap']),
        onTrack: j['on_track'] as bool? ?? false,
        year: j['year'] as int?,
        competitionRatio: (j['competition_ratio'] as num?)?.toDouble(),
      );
  final double passingScore;
  final double gap;
  final bool onTrack;
  final int? year;
  final double? competitionRatio;
}

class AttemptResult {
  const AttemptResult({
    required this.total,
    required this.maxTotal,
    required this.correct,
    required this.questions,
    required this.subjectScores,
    required this.review,
    this.comparison,
  });
  factory AttemptResult.fromJson(Json j) => AttemptResult(
        total: _num(j['total']),
        maxTotal: _num(j['max_total']),
        correct: _int(j['correct']),
        questions: _int(j['questions']),
        subjectScores: {for (final e in _json(j['subject_scores']).entries) e.key: _num(e.value)},
        review: _list(j['review']).map(ReviewRow.fromJson).toList(),
        comparison: _jsonOpt(j['comparison']) == null ? null : Comparison.fromJson(_json(j['comparison'])),
      );
  final double total;
  final double maxTotal;
  final int correct;
  final int questions;
  final Map<String, double> subjectScores;
  final List<ReviewRow> review;
  final Comparison? comparison;
}

class HistoryItem {
  const HistoryItem({required this.attemptId, required this.score, required this.maxTotal, required this.kind, this.submittedAt});
  factory HistoryItem.fromJson(Json j) => HistoryItem(
        attemptId: '${j['attempt_id']}',
        score: _num(j['score']),
        maxTotal: _num(j['max_total']),
        kind: '${j['kind']}',
        submittedAt: DateTime.tryParse('${j['submitted_at'] ?? ''}')?.toLocal(),
      );
  final String attemptId;
  final double score;
  final double maxTotal;
  final String kind;
  final DateTime? submittedAt;
}

class Prediction {
  const Prediction({required this.value, required this.low, required this.high, required this.attempts, required this.confident, this.comparison});
  final double value;
  final double low;
  final double high;
  final int attempts;
  final bool confident;
  final Comparison? comparison;
}

Prediction? predictionFromJson(Json j) {
  final p = _jsonOpt(j['prediction']);
  if (p == null) return null;
  return Prediction(
    value: _num(p['value']),
    low: _num(p['low']),
    high: _num(p['high']),
    attempts: _int(p['attempts']),
    confident: p['confident'] as bool? ?? false,
    comparison: _jsonOpt(j['comparison']) == null ? null : Comparison.fromJson(_json(j['comparison'])),
  );
}

class Quest {
  const Quest({required this.id, required this.title, required this.progress, required this.target, required this.completed, required this.rewardXp, required this.rewardGems});
  factory Quest.fromJson(Json j) => Quest(
        id: j['id'] as String,
        title: _names(j['title']),
        progress: _int(j['progress']),
        target: _int(j['target']),
        completed: j['completed'] as bool? ?? false,
        rewardXp: _int(j['reward_xp']),
        rewardGems: _int(j['reward_gems']),
      );
  final String id;
  final Map<String, String> title;
  final int progress;
  final int target;
  final bool completed;
  final int rewardXp;
  final int rewardGems;
}

class LeagueRow {
  const LeagueRow({required this.userId, required this.name, required this.rank, required this.xp, required this.isMe, required this.zone});
  factory LeagueRow.fromJson(Json j) => LeagueRow(
        userId: '${j['user_id']}',
        name: '${j['name']}',
        rank: _int(j['rank']),
        xp: _int(j['xp']),
        isMe: j['is_me'] as bool? ?? false,
        zone: '${j['zone']}',
      );
  final String userId;
  final String name;
  final int rank;
  final int xp;
  final bool isMe;
  final String zone;
}

class League {
  const League({required this.tier, required this.rows, this.endsAt});
  factory League.fromJson(Json j) => League(
        tier: _jsonOpt(j['tier']) == null ? null : LeagueTier.fromJson(_json(j['tier'])),
        rows: _list(j['rows']).map(LeagueRow.fromJson).toList(),
        endsAt: DateTime.tryParse('${j['ends_at'] ?? ''}')?.toLocal(),
      );
  final LeagueTier? tier;
  final List<LeagueRow> rows;
  final DateTime? endsAt;
}

class LeaderRow {
  const LeaderRow({required this.userId, required this.name, required this.xp});
  factory LeaderRow.fromJson(Json j) => LeaderRow(userId: '${j['user_id']}', name: '${j['name']}', xp: _int(j['xp']));
  final String userId;
  final String name;
  final int xp;
}

/// `GET /v1/gamification/leaderboard/{friends|lyceum}`.
class Board {
  const Board({required this.rows, this.myRank});
  factory Board.fromJson(Json j) => Board(rows: _list(j['rows']).map(LeaderRow.fromJson).toList(), myRank: j['my_rank'] as int?);
  final List<LeaderRow> rows;
  final int? myRank;
}

/// `GET|PUT /v1/notify/preferences`.
class NotifyPrefs {
  const NotifyPrefs({
    required this.enabled,
    required this.channels,
    required this.kinds,
    required this.maxPerDay,
    required this.quietStart,
    required this.quietEnd,
  });
  factory NotifyPrefs.fromJson(Json j) => NotifyPrefs(
        enabled: j['enabled'] as bool? ?? true,
        channels: _strs(j['channels']),
        kinds: _strs(j['kinds']),
        maxPerDay: _int(j['max_per_day']),
        quietStart: '${j['quiet_start'] ?? '22:00:00'}',
        quietEnd: '${j['quiet_end'] ?? '08:00:00'}',
      );
  Json toJson() => {
        'enabled': enabled,
        'channels': channels,
        'kinds': kinds,
        'max_per_day': maxPerDay,
        'quiet_start': quietStart,
        'quiet_end': quietEnd,
      };
  NotifyPrefs copyWith({bool? enabled, List<String>? channels, List<String>? kinds, int? maxPerDay}) => NotifyPrefs(
        enabled: enabled ?? this.enabled,
        channels: channels ?? this.channels,
        kinds: kinds ?? this.kinds,
        maxPerDay: maxPerDay ?? this.maxPerDay,
        quietStart: quietStart,
        quietEnd: quietEnd,
      );
  final bool enabled;
  final List<String> channels;
  final List<String> kinds;
  final int maxPerDay;
  final String quietStart;
  final String quietEnd;
}

class Friend {
  const Friend({required this.userId, required this.name, required this.xp});
  factory Friend.fromJson(Json j) => Friend(userId: '${j['user_id']}', name: '${j['name']}', xp: _int(j['xp']));
  final String userId;
  final String name;
  final int xp;
}

class Lyceum {
  const Lyceum({required this.id, required this.names, required this.quota, required this.applications, this.competitionRatio, this.latestYear});
  factory Lyceum.fromJson(Json j) => Lyceum(
        id: j['id'] as String,
        names: _names(j['names']),
        quota: _int(j['quota']),
        applications: _int(j['applications']),
        competitionRatio: (j['competition_ratio'] as num?)?.toDouble(),
        latestYear: j['latest_year'] as int?,
      );
  final String id;
  final Map<String, String> names;
  final int quota;
  final int applications;
  final double? competitionRatio;
  final int? latestYear;
}

class SpecialityStat {
  const SpecialityStat({required this.year, required this.languageId, required this.name, required this.quota, required this.applications, this.passingScore, this.competitionRatio});
  factory SpecialityStat.fromJson(Json j) => SpecialityStat(
        year: _int(j['year']),
        languageId: j['language_id'] as String?,
        name: '${j['name'] ?? ''}',
        quota: _int(j['quota']),
        applications: _int(j['applications']),
        passingScore: (j['passing_score'] as num?)?.toDouble(),
        competitionRatio: (j['competition_ratio'] as num?)?.toDouble(),
      );
  final int year;
  final String? languageId;
  final String name;
  final int quota;
  final int applications;
  final double? passingScore;
  final double? competitionRatio;
}

class LyceumDetail {
  const LyceumDetail({required this.id, required this.names, required this.stats});
  factory LyceumDetail.fromJson(Json j) => LyceumDetail(
        id: j['id'] as String,
        names: _names(j['names']),
        stats: _list(j['stats']).map(SpecialityStat.fromJson).toList(),
      );
  final String id;
  final Map<String, String> names;
  final List<SpecialityStat> stats;
}

class EduLanguage {
  const EduLanguage({required this.id, required this.code, required this.names});
  factory EduLanguage.fromJson(Json j) => EduLanguage(id: j['id'] as String, code: '${j['code']}', names: _names(j['names']));
  final String id;
  final String code;
  final Map<String, String> names;
}

class Plan {
  const Plan({required this.code, required this.names, required this.periodMonths, required this.priceUzs});
  factory Plan.fromJson(Json j) => Plan(
        code: '${j['code']}',
        names: _names(j['names']),
        periodMonths: _int(j['period_months']),
        priceUzs: _int(j['price_uzs']),
      );
  final String code;
  final Map<String, String> names;
  final int periodMonths;
  final int priceUzs;
}

/// `GET /v1/billing/me` — entitlement status only (payments happen on the web).
class Billing {
  const Billing({required this.planCode, required this.features, this.status, this.until});
  factory Billing.fromJson(Json j) {
    final ent = _json(j['entitlements']);
    final sub = _jsonOpt(j['subscription']);
    return Billing(
      planCode: '${ent['plan_code'] ?? 'free'}',
      features: _strs(ent['features']),
      status: sub?['status'] as String?,
      until: DateTime.tryParse('${sub?['until'] ?? ''}')?.toLocal(),
    );
  }
  final String planCode;
  final List<String> features;
  final String? status;
  final DateTime? until;
  bool get isPremium => planCode != 'free';
}
