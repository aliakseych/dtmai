from aiogram.filters.callback_data import CallbackData


class OpenBank(CallbackData, prefix="bank_open"):
    pass


class SelectBankSubject(CallbackData, prefix="bank_subj"):
    subject: str


class ToggleBankLevel(CallbackData, prefix="bank_lvl"):
    level: str  # empty string means "clear"


class ToggleBankSolved(CallbackData, prefix="bank_slv"):
    value: str  # "all" | "solved" | "unsolved"


class ApplyBankFilter(CallbackData, prefix="bank_apply"):
    pass


class ShowBankAll(CallbackData, prefix="bank_all"):
    pass


class BankPage(CallbackData, prefix="bank_pg"):
    page: int


class BackToBankFilter(CallbackData, prefix="bank_back"):
    pass


class ViewBankQuestion(CallbackData, prefix="bank_view"):
    question_id: str


class BankPrevQuestion(CallbackData, prefix="bank_prev"):
    pass


class BankNextQuestion(CallbackData, prefix="bank_next"):
    pass


class ShowBankAnswer(CallbackData, prefix="bank_show_ans"):
    pass


class BackToBankList(CallbackData, prefix="bank_list"):
    page: int