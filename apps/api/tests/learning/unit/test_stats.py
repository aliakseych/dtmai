from datetime import date
from uuid import uuid4

from app.modules.learning.domain.stats import Progress, SubjectAnswers, build_stats

TODAY = date(2026, 3, 31)


def test_series_is_zero_filled_oldest_first_and_accuracy_spans_all_answers():
    sid = uuid4()
    stats = build_stats(
        Progress(100, 3, 7, 5, {TODAY: 40}),
        {TODAY: (4, 3)},
        [SubjectAnswers(sid, 10, 5, 0.6), SubjectAnswers(None, 10, 5, None)],
        [],
        TODAY,
    )
    assert len(stats.daily) == 30
    assert stats.daily[-1].date == TODAY and stats.daily[0].date < stats.daily[1].date
    assert (stats.daily[-1].xp, stats.daily[-1].answered, stats.daily[-1].correct) == (40, 4, 3)
    assert stats.daily[0].xp == 0
    assert stats.accuracy == 0.5
    assert [s.subject_id for s in stats.by_subject] == [sid]
    assert stats.by_subject[0].mastery == 0.6
    assert stats.streak_best == 7


def test_no_answers_gives_zero_accuracy():
    assert build_stats(Progress(0, 0, 0, 0, {}), {}, [], [], TODAY).accuracy == 0.0
