from app.shared.errors import Conflict, NotFound, ValidationFailed


class PlanNotFound(NotFound):
    code = "plan_not_found"


class TaskNotFound(NotFound):
    code = "task_not_found"


class DirectionNotFound(NotFound):
    code = "direction_not_found"


class TaskAlreadyDone(Conflict):
    code = "task_already_done"


class TaskNotUndoable(Conflict):
    code = "task_not_undoable"


class QuestionNotInSet(NotFound):
    code = "daily_question_not_found"


class DailyQuestionAnswered(Conflict):
    code = "daily_question_answered"


class ExamDateTooSoon(ValidationFailed):
    code = "exam_date_too_soon"


class NoActiveSubjects(ValidationFailed):
    code = "no_active_subjects"
