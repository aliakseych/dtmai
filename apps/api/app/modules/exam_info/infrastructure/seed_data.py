"""Initial exam data (2027 academic-lyceum exam). Seeded once; afterwards admins own it."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Final
from uuid import NAMESPACE_URL, UUID, uuid5

from app.modules.exam_info.domain.models import (
    FOREIGN_LANGUAGE_GROUP,
    LYCEUM_IQ_POINTS,
    LYCEUM_QUESTIONS,
    LYCEUM_SUBJECT_POINTS,
)

EXAM_YEAR: Final = 2027
SOURCE_URL: Final = "https://lex.uz/uz/docs/-6973011"
EXAM_DATE: Final = date(2027, 7, 25)  # unverified: the Agency has not announced it
# Languages a candidate may pick as the "foreign language" exam subject.
FOREIGN_LANGUAGE_CODES: Final = (
    "english",
    "german",
    "french",
    "arabic",
    "turkish",
    "chinese",
    "korean",
    "japanese",
)

Texts = dict[str, str]


def t(en: str, ru: str, lat: str, cyr: str) -> Texts:
    return {"en": en, "ru": ru, "uz-Latn": lat, "uz-Cyrl": cyr}


def sid(*parts: str) -> UUID:
    """Deterministic id so reruns hit ON CONFLICT instead of duplicating."""
    return uuid5(NAMESPACE_URL, "dtmai:exam_info:" + ":".join(parts))


# --- section labels ---------------------------------------------------------------
LABELS: Final[dict[str, Texts]] = {
    "math": t("Mathematics", "Математика", "Matematika", "Математика"),
    "physics": t("Physics", "Физика", "Fizika", "Физика"),
    "foreign": t("Foreign language", "Иностранный язык", "Xorijiy til", "Хорижий тил"),
    "native": t(
        "Native language and literature",
        "Родной язык и литература",
        "Ona tili va adabiyot",
        "Она тили ва адабиёт",
    ),
    "geography": t("Geography", "География", "Geografiya", "География"),
    "biology": t("Biology", "Биология", "Biologiya", "Биология"),
    "chemistry": t("Chemistry", "Химия", "Kimyo", "Кимё"),
    "history": t("History", "История", "Tarix", "Тарих"),
    "law": t("Law", "Правоведение", "Huquqshunoslik", "Ҳуқуқшунослик"),
    "iq": t("IQ", "IQ (логика)", "IQ", "IQ"),
    "drawing": t(
        "Drawing and technical drawing",
        "Рисунок и черчение",
        "Rasm va chizmachilik",
        "Расм ва чизмачилик",
    ),
}
# label key -> catalog subject code ("foreign" is a choice group, "drawing" has no app subject).
SUBJECT_CODES: Final[dict[str, str]] = {
    "math": "math",
    "physics": "physics",
    "native": "native_language",
    "geography": "geography",
    "biology": "biology",
    "chemistry": "chemistry",
    "history": "history",
    "law": "law",
    "iq": "iq",
}

GROUP_NAMES: Final[dict[str, Texts]] = {
    "aniq": t("Exact sciences-{n}", "Точные науки-{n}", "Aniq fanlar-{n}", "Аниқ фанлар-{n}"),
    "tabiiy": t(
        "Natural sciences-{n}", "Естественные науки-{n}", "Tabiiy fanlar-{n}", "Табиий фанлар-{n}"
    ),
    "ijtimoiy": t(
        "Social sciences and humanities-{n}",
        "Общественно-гуманитарные науки-{n}",
        "Ijtimoiy-gumanitar fanlar-{n}",
        "Ижтимоий-гуманитар фанлар-{n}",
    ),
    "tillar": t("Foreign languages", "Иностранные языки", "Xorijiy tillar", "Хорижий тиллар"),
}

# (direction_code, group, number, (field subject 1, field subject 2)) per §12 of the design.
DIRECTIONS: Final[tuple[tuple[str, str, int, tuple[str, str]], ...]] = (
    ("3910001", "aniq", 1, ("math", "physics")),
    ("3910002", "aniq", 2, ("math", "foreign")),
    ("3910003", "aniq", 3, ("math", "drawing")),
    ("3910004", "aniq", 4, ("math", "native")),
    ("3910005", "aniq", 5, ("math", "geography")),
    ("3920001", "tabiiy", 1, ("biology", "chemistry")),
    ("3920002", "tabiiy", 2, ("chemistry", "math")),
    ("3930001", "ijtimoiy", 1, ("native", "foreign")),
    ("3930002", "ijtimoiy", 2, ("history", "foreign")),
    ("3930003", "ijtimoiy", 3, ("native", "biology")),
    ("3930004", "ijtimoiy", 4, ("history", "geography")),
    ("3930005", "ijtimoiy", 5, ("law", "foreign")),
    ("3940000", "tillar", 0, ("foreign", "native")),
)


@dataclass(frozen=True, slots=True)
class SectionSpec:
    id: UUID
    role: str
    slot: int
    label_key: str
    names: Texts
    subject_code: str | None
    choice_group: str | None
    question_count: int | None
    points_per_question: Decimal | None
    max_points: Decimal
    exemptible: bool


@dataclass(frozen=True, slots=True)
class ProfileSpec:
    id: UUID
    code: str
    direction_code: str
    group_code: str
    names: Texts
    position: int
    sections: tuple[SectionSpec, ...]


def _section(profile_code: str, slot: int, label_key: str) -> SectionSpec:
    sec_id = sid("section", profile_code, str(slot))
    names = LABELS[label_key]
    if label_key == "iq":
        return SectionSpec(
            sec_id, "iq", 0, label_key, names, SUBJECT_CODES["iq"], None,
            LYCEUM_QUESTIONS, LYCEUM_IQ_POINTS, LYCEUM_QUESTIONS * LYCEUM_IQ_POINTS, False,
        )  # fmt: skip
    if label_key == "drawing":
        # Creative exam: format and points are unpublished, 62 is assumed to keep the 146 total.
        return SectionSpec(
            sec_id, "creative", slot, label_key, names, None, None,
            None, None, LYCEUM_QUESTIONS * LYCEUM_SUBJECT_POINTS, False,
        )  # fmt: skip
    foreign = label_key == "foreign"
    return SectionSpec(
        sec_id, "subject", slot, label_key, names,
        None if foreign else SUBJECT_CODES[label_key],
        FOREIGN_LANGUAGE_GROUP if foreign else None,
        LYCEUM_QUESTIONS, LYCEUM_SUBJECT_POINTS, LYCEUM_QUESTIONS * LYCEUM_SUBJECT_POINTS, True,
    )  # fmt: skip


def profile_specs() -> tuple[ProfileSpec, ...]:
    out: list[ProfileSpec] = []
    for pos, (direction, group, n, subjects) in enumerate(DIRECTIONS):
        code = f"lyceum_{direction}"
        names = {loc: txt.format(n=n) for loc, txt in GROUP_NAMES[group].items()}
        sections = (
            _section(code, 0, "iq"),
            _section(code, 1, subjects[0]),
            _section(code, 2, subjects[1]),
        )
        out.append(ProfileSpec(sid("profile", code), code, direction, group, names, pos, sections))
    return tuple(out)


# --- certificates (§11.4) ----------------------------------------------------------
@dataclass(frozen=True, slots=True)
class CertSpec:
    cert_type: str
    level_label: str
    min_value: Decimal | None
    verified: bool
    active: bool
    note: Texts


_NO_NOTE: Final = t("", "", "", "")
LANGUAGE_CERTS: Final[tuple[CertSpec, ...]] = (
    CertSpec("ielts", "IELTS 5.0", Decimal("5.0"), True, True, _NO_NOTE),
    CertSpec("toefl", "TOEFL iBT 42", Decimal("42"), True, True, _NO_NOTE),
    CertSpec(
        "cefr", "B1", Decimal(3), True, True,
        t(
            "B1 or higher: Cambridge PET, Goethe, DELF, TCF and similar.",
            "B1 и выше: Cambridge PET, Goethe, DELF, TCF и аналогичные.",
            "B1 va undan yuqori: Cambridge PET, Goethe, DELF, TCF va shunga oʼxshash.",
            "B1 ва ундан юқори: Cambridge PET, Goethe, DELF, TCF ва шунга ўхшаш.",
        ),
    ),
    CertSpec(
        "national", "National certificate 38", Decimal(38), False, True,
        t(
            "Threshold not confirmed by the Agency; check before relying on it.",
            "Порог не подтверждён Агентством; проверьте, прежде чем полагаться на него.",
            "Chegara Agentlik tomonidan tasdiqlanmagan; tayanishdan oldin tekshiring.",
            "Чегара Агентлик томонидан тасдиқланмаган; таяниш олдидан текширинг.",
        ),
    ),
)  # fmt: skip
SUBJECT_CERT: Final = CertSpec(
    "national", "National certificate", None, False, False,
    t(
        "The minimum is set by the Agency and not yet published; an admin enables this rule.",
        "Минимум задаёт Агентство, он пока не опубликован; правило включает администратор.",
        "Minimal ball Agentlik tomonidan belgilanadi va hali eʼlon qilinmagan; qoidani admin yoqadi.",
        "Минимал балл Агентлик томонидан белгиланади ва ҳали эълон қилинмаган; қоидани админ ёқади.",
    ),
)  # fmt: skip


# --- events --------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class EventSpec:
    kind: str
    starts_on: date
    ends_on: date | None
    label: Texts
    position: int


EVENTS: Final[tuple[EventSpec, ...]] = (
    EventSpec(
        "applications", date(2027, 6, 10), date(2027, 7, 10),
        t("Applications (my.gov.uz)", "Подача заявлений (my.gov.uz)",
          "Arizalar qabuli (my.gov.uz)", "Аризалар қабули (my.gov.uz)"), 0,
    ),
    EventSpec(
        "test", date(2027, 7, 25), date(2027, 7, 26),
        t("Entrance test", "Вступительный тест", "Kirish testi", "Кириш тести"), 1,
    ),
    EventSpec(
        "results", date(2027, 7, 30), None,
        t("Results announced", "Объявление результатов", "Natijalar eʼlon qilinadi",
          "Натижалар эълон қилинади"), 2,
    ),
    EventSpec(
        "appeal", date(2027, 7, 30), date(2027, 8, 4),
        t("Appeals", "Апелляция", "Apellyatsiya", "Апелляция"), 3,
    ),
)  # fmt: skip


# --- FAQ -------------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class FaqSpec:
    key: str
    category: str
    verified: bool
    question: Texts
    answer: Texts
    position: int


def _faq(pos: int, key: str, cat: str, verified: bool, q: Texts, a: Texts) -> FaqSpec:
    return FaqSpec(key, cat, verified, q, a, pos)


FAQ: Final[tuple[FaqSpec, ...]] = (
    _faq(
        0, "exam_dates", "dates", False,
        t("When is the exam?", "Когда экзамен?", "Imtihon qachon?", "Имтиҳон қачон?"),
        t(
            "The 2027 test is expected on 25–26 July. The date is not announced yet: in 2026 the test was "
            "on 24–25 July and applications opened on 10 June, so we plan with the same pattern.",
            "Тест 2027 года ожидается 25–26 июля. Дата пока не объявлена: в 2026 году тест прошёл "
            "24–25 июля, а приём заявлений начался 10 июня, поэтому мы планируем по той же схеме.",
            "2027-yilgi test 25–26-iyulda kutilmoqda. Sana hali eʼlon qilinmagan: 2026-yilda test "
            "24–25-iyulda bo‘lgan, arizalar 10-iyundan qabul qilingan, shuning uchun shu tartibda rejalashtiramiz.",
            "2027 йилги тест 25–26 июлда кутилмоқда. Сана ҳали эълон қилинмаган: 2026 йилда тест "
            "24–25 июлда бўлган, аризалар 10 июндан қабул қилинган, шунинг учун шу тартибда режалаштирамиз.",
        ),
    ),
    _faq(
        1, "exam_subjects", "subjects", True,
        t("Which subjects are on the exam?", "Какие предметы на экзамене?",
          "Imtihonda qaysi fanlar bor?", "Имтиҳонда қайси фанлар бор?"),
        t(
            "IQ plus two field subjects. There are 13 directions; the pair of subjects depends on the "
            "direction. The foreign language is chosen at application. Pairs may change from year to year.",
            "IQ и два профильных предмета. Всего 13 направлений; пара предметов зависит от направления. "
            "Иностранный язык выбирается при подаче заявления. Пары могут меняться из года в год.",
            "IQ va ikkita yo‘nalish fani. Jami 13 ta yo‘nalish bor; fanlar juftligi yo‘nalishga bog‘liq. "
            "Xorijiy til ariza topshirishda tanlanadi. Juftliklar yildan yilga o‘zgarishi mumkin.",
            "IQ ва иккита йўналиш фани. Жами 13 та йўналиш бор; фанлар жуфтлиги йўналишга боғлиқ. "
            "Хорижий тил ариза топширишда танланади. Жуфтликлар йилдан йилга ўзгариши мумкин.",
        ),
    ),
    _faq(
        2, "exam_points", "scoring", True,
        t("How many questions and points?", "Сколько вопросов и баллов?",
          "Nechta savol va ball?", "Нечта савол ва балл?"),
        t(
            "60 questions, 146 points in total: 20 × 3.1 = 62 for each field subject, and 20 × 1.1 = 22 for IQ.",
            "60 вопросов, всего 146 баллов: по 20 × 3,1 = 62 за каждый профильный предмет и 20 × 1,1 = 22 за IQ.",
            "60 ta savol, jami 146 ball: har bir yo‘nalish fani uchun 20 × 3,1 = 62, IQ uchun 20 × 1,1 = 22.",
            "60 та савол, жами 146 балл: ҳар бир йўналиш фани учун 20 × 3,1 = 62, IQ учун 20 × 1,1 = 22.",
        ),
    ),
    _faq(
        3, "exam_iq", "scoring", True,
        t("How is IQ scored?", "Как оценивается IQ?", "IQ qanday baholanadi?", "IQ қандай баҳоланади?"),
        t(
            "20 questions × 1.1 = 22 points. It is the same in every direction and is never waived by a certificate.",
            "20 вопросов × 1,1 = 22 балла. Одинаково для всех направлений; сертификат от IQ не освобождает.",
            "20 ta savol × 1,1 = 22 ball. Barcha yo‘nalishlarda bir xil; sertifikat IQ dan ozod qilmaydi.",
            "20 та савол × 1,1 = 22 балл. Барча йўналишларда бир хил; сертификат IQ дан озод қилмайди.",
        ),
    ),
    _faq(
        4, "exam_certificates", "certificates", True,
        t("Can a certificate replace an exam subject?", "Может ли сертификат заменить предмет?",
          "Sertifikat fanni almashtira oladimi?", "Сертификат фанни алмаштира оладими?"),
        t(
            "Yes, for a field subject you get the full 62 points. Foreign language: IELTS 5.0+, TOEFL iBT 42+, "
            "or CEFR B1+ (Cambridge PET, Goethe, DELF, TCF). Other subjects need a National certificate; the "
            "minimum is set by the Agency and not published. IQ is never waived.",
            "Да, за профильный предмет начисляются полные 62 балла. Иностранный язык: IELTS от 5.0, TOEFL iBT "
            "от 42 или CEFR от B1 (Cambridge PET, Goethe, DELF, TCF). Для других предметов нужен национальный "
            "сертификат; минимум задаёт Агентство, он не опубликован. От IQ не освобождают.",
            "Ha, yo‘nalish fani uchun to‘liq 62 ball beriladi. Xorijiy til: IELTS 5.0+, TOEFL iBT 42+ yoki CEFR "
            "B1+ (Cambridge PET, Goethe, DELF, TCF). Boshqa fanlar uchun milliy sertifikat kerak; minimal ballni "
            "Agentlik belgilaydi, u eʼlon qilinmagan. IQ dan hech qachon ozod qilinmaydi.",
            "Ҳа, йўналиш фани учун тўлиқ 62 балл берилади. Хорижий тил: IELTS 5.0+, TOEFL iBT 42+ ёки CEFR B1+ "
            "(Cambridge PET, Goethe, DELF, TCF). Бошқа фанлар учун миллий сертификат керак; минимал баллни "
            "Агентлик белгилайди, у эълон қилинмаган. IQ дан ҳеч қачон озод қилинмайди.",
        ),
    ),
    _faq(
        5, "exam_lyceums", "application", True,
        t("How many lyceums can I apply to?", "Сколько лицеев можно выбрать?",
          "Nechta litseyga ariza berish mumkin?", "Нечта лицейга ариза бериш мумкин?"),
        t(
            "Up to 3 lyceums, one direction in each, all with the same language of instruction. Apply on "
            "my.gov.uz and choose the exam region there.",
            "До 3 лицеев, в каждом одно направление, язык обучения у всех одинаковый. Заявление подаётся на "
            "my.gov.uz, там же выбирается регион сдачи.",
            "3 tagacha litsey, har birida bitta yo‘nalish, taʼlim tili bir xil. Ariza my.gov.uz orqali "
            "topshiriladi, imtihon hududi ham shu yerda tanlanadi.",
            "3 тагача лицей, ҳар бирида битта йўналиш, таълим тили бир хил. Ариза my.gov.uz орқали "
            "топширилади, имтиҳон ҳудуди ҳам шу ерда танланади.",
        ),
    ),
    _faq(
        6, "exam_language", "application", True,
        t("Which languages can I choose?", "Какие языки можно выбрать?",
          "Qaysi tillarni tanlash mumkin?", "Қайси тилларни танлаш мумкин?"),
        t(
            "Instruction is in Uzbek, Russian or Karakalpak. The foreign language is one of English, German, "
            "French, Arabic, Turkish, Chinese, Korean or Japanese.",
            "Обучение ведётся на узбекском, русском или каракалпакском. Иностранный язык: английский, немецкий, "
            "французский, арабский, турецкий, китайский, корейский или японский.",
            "Taʼlim o‘zbek, rus yoki qoraqalpoq tilida. Xorijiy til: ingliz, nemis, fransuz, arab, turk, xitoy, "
            "koreys yoki yapon tili.",
            "Таълим ўзбек, рус ёки қорақалпоқ тилида. Хорижий тил: инглиз, немис, француз, араб, турк, хитой, "
            "корейс ёки япон тили.",
        ),
    ),
    _faq(
        7, "exam_appeal", "dates", False,
        t("Can I appeal my result?", "Можно ли подать апелляцию?",
          "Natijaga apellyatsiya berish mumkinmi?", "Натижага апелляция бериш мумкинми?"),
        t(
            "In 2026 an electronic appeal had to be filed within 3 working days of the results and was reviewed "
            "about two weeks later. Expect a similar process in 2027.",
            "В 2026 году электронная апелляция подавалась в течение 3 рабочих дней после результатов и "
            "рассматривалась примерно через две недели. В 2027 году ожидайте похожий порядок.",
            "2026-yilda elektron apellyatsiya natijalardan keyin 3 ish kuni ichida berilgan va taxminan ikki "
            "haftadan so‘ng ko‘rib chiqilgan. 2027-yilda ham shunga o‘xshash tartib kutiladi.",
            "2026 йилда электрон апелляция натижалардан кейин 3 иш куни ичида берилган ва тахминан икки "
            "ҳафтадан сўнг кўриб чиқилган. 2027 йилда ҳам шунга ўхшаш тартиб кутилади.",
        ),
    ),
    _faq(
        8, "exam_reapply", "reapply", False,
        t("Can I retake the exam?", "Можно ли пересдать экзамен?",
          "Imtihonni qayta topshirish mumkinmi?", "Имтиҳонни қайта топшириш мумкинми?"),
        t(
            "No retake rule has been confirmed. Treat it as one attempt per year; creative exams cannot be "
            "retaken. Confirm with the Agency.",
            "Правило пересдачи не подтверждено. Считайте, что попытка одна в год; творческие экзамены "
            "пересдать нельзя. Уточните в Агентстве.",
            "Qayta topshirish qoidasi tasdiqlanmagan. Yiliga bitta urinish deb hisoblang; ijodiy imtihonlarni "
            "qayta topshirib bo‘lmaydi. Agentlikdan aniqlang.",
            "Қайта топшириш қоидаси тасдиқланмаган. Йилига битта уриниш деб ҳисобланг; ижодий имтиҳонларни "
            "қайта топшириб бўлмайди. Агентликдан аниқланг.",
        ),
    ),
    _faq(
        9, "exam_creative", "subjects", False,
        t("What about Exact sciences-3 (drawing)?", "Что с направлением «Точные науки-3» (рисунок)?",
          "Aniq fanlar-3 (rasm) yo‘nalishi-chi?", "Аниқ фанлар-3 (расм) йўналиши-чи?"),
        t(
            "It is mathematics plus Drawing and technical drawing. The points and format of the drawing part "
            "are not published and it cannot be retaken. The app covers mathematics and IQ only.",
            "Это математика плюс «Рисунок и черчение». Баллы и формат творческой части не опубликованы, "
            "пересдать её нельзя. Приложение готовит только к математике и IQ.",
            "Bu matematika va Rasm va chizmachilik. Ijodiy qism ballari va formati eʼlon qilinmagan, uni "
            "qayta topshirib bo‘lmaydi. Ilova faqat matematika va IQ ga tayyorlaydi.",
            "Бу математика ва Расм ва чизмачилик. Ижодий қисм баллари ва формати эълон қилинмаган, уни "
            "қайта топшириб бўлмайди. Илова фақат математика ва IQ га тайёрлайди.",
        ),
    ),
)  # fmt: skip
