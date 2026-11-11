from datetime import UTC, datetime
from urllib.parse import quote

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.interfaces.bot import keyboards
from app.interfaces.bot.i18n import (
    CONTENT_LANGUAGE,
    DEFAULT_LOCALE,
    LOCALES,
    locale_from_telegram,
    t,
)
from app.modules.bank import facade as bank
from app.modules.catalog import facade as catalog
from app.modules.notify.domain.policy import Channel, Preferences
from app.modules.notify.infrastructure.repositories import SqlNotifyRepo
from app.modules.notify.settings import get_notify_settings
from app.shared.db import get_sessionmaker

router = Router(name="dtmai")

LINK_PREFIX = "link_"


def _app_url(payload: str | None = None) -> str:
    base = get_notify_settings().telegram_mini_app_url
    return f"{base}?start={quote(payload, safe='')}" if payload else base


async def _locale(session: AsyncSession, chat_id: int, language_code: str | None) -> str:
    chat = await SqlNotifyRepo(session).chat(chat_id)
    return chat.locale if chat else locale_from_telegram(language_code)


async def _menu(session: AsyncSession, chat_id: int, locale: str, payload: str | None = None):  # type: ignore[no-untyped-def]
    repo = SqlNotifyRepo(session)
    user_id = await repo.user_for_chat(chat_id)
    on = False
    if user_id is not None:
        p = await repo.get_preferences(user_id)
        on = p.enabled and Channel.TELEGRAM in p.channels
    return keyboards.main_menu(locale, _app_url(payload), reminders_on=on)


@router.message(Command("start"))
async def on_start(message: Message, command: CommandObject) -> None:
    if message.from_user is None:
        return
    chat_id = message.chat.id
    payload = (command.args or "").strip() or None
    async with get_sessionmaker()() as session:
        repo = SqlNotifyRepo(session)
        existing = await repo.chat(chat_id)
        locale = existing.locale if existing else locale_from_telegram(message.from_user.language_code)
        await repo.upsert_chat(chat_id, locale)
        linked: bool | None = None
        if payload and payload.startswith(LINK_PREFIX):
            user_id = await repo.consume_link_code(
                payload[len(LINK_PREFIX):], chat_id, datetime.now(UTC)
            )
            linked = user_id is not None
            payload = None
        menu = await _menu(session, chat_id, locale, payload)
        await session.commit()
    if linked is not None:
        await message.answer(t(locale, "link_ok" if linked else "link_bad"))
    await message.answer(t(locale, "welcome", name=message.from_user.first_name), reply_markup=menu)


@router.callback_query(F.data == keyboards.MENU_HELP)
async def on_help(cb: CallbackQuery) -> None:
    if not isinstance(cb.message, Message):
        return await cb.answer()
    async with get_sessionmaker()() as session:
        locale = await _locale(session, cb.message.chat.id, cb.from_user.language_code)
    await cb.message.answer(t(locale, "help_text"))
    await cb.answer()


@router.callback_query(F.data == keyboards.MENU_LANG)
async def on_language_menu(cb: CallbackQuery) -> None:
    if not isinstance(cb.message, Message):
        return await cb.answer()
    async with get_sessionmaker()() as session:
        locale = await _locale(session, cb.message.chat.id, cb.from_user.language_code)
    await cb.message.answer(t(locale, "pick_language"), reply_markup=keyboards.language_menu())
    await cb.answer()


@router.callback_query(F.data.startswith(f"{keyboards.PREFIX_LANG}:"))
async def on_language_set(cb: CallbackQuery) -> None:
    if not isinstance(cb.message, Message) or cb.data is None:
        return await cb.answer()
    locale = cb.data.split(":", 1)[1]
    if locale not in LOCALES:
        return await cb.answer()
    async with get_sessionmaker()() as session:
        await SqlNotifyRepo(session).upsert_chat(cb.message.chat.id, locale)
        menu = await _menu(session, cb.message.chat.id, locale)
        await session.commit()
    await cb.message.answer(t(locale, "language_saved"), reply_markup=menu)
    await cb.answer()


@router.callback_query(F.data == keyboards.MENU_REMINDERS)
async def on_reminders(cb: CallbackQuery) -> None:
    if not isinstance(cb.message, Message):
        return await cb.answer()
    chat_id = cb.message.chat.id
    async with get_sessionmaker()() as session:
        repo = SqlNotifyRepo(session)
        locale = await _locale(session, chat_id, cb.from_user.language_code)
        user_id = await repo.user_for_chat(chat_id)
        if user_id is None:
            return await cb.answer(t(locale, "need_link"), show_alert=True)
        prefs = await repo.get_preferences(user_id)
        turn_on = not (prefs.enabled and Channel.TELEGRAM in prefs.channels)
        updated = Preferences(
            user_id=user_id, enabled=turn_on if turn_on else prefs.enabled,
            channels=(prefs.channels | {Channel.TELEGRAM}) if turn_on
            else prefs.channels - {Channel.TELEGRAM},
            kinds=prefs.kinds, quiet_start=prefs.quiet_start, quiet_end=prefs.quiet_end,
            max_per_day=prefs.max_per_day,
        )
        await repo.save_preferences(updated)
        menu = await _menu(session, chat_id, locale)
        await session.commit()
    await cb.message.edit_reply_markup(reply_markup=menu)
    await cb.answer(t(locale, "reminders_enabled" if turn_on else "reminders_disabled"))


@router.callback_query(F.data == keyboards.MENU_DAILY)
@router.message(Command("daily"))
async def on_daily(event: CallbackQuery | Message) -> None:
    msg = event.message if isinstance(event, CallbackQuery) else event
    if not isinstance(msg, Message):
        return
    lang_code = event.from_user.language_code if event.from_user else None
    async with get_sessionmaker()() as session:
        locale = await _locale(session, msg.chat.id, lang_code)
        question = await _pick_daily(session, CONTENT_LANGUAGE.get(locale, "uz"))
    if isinstance(event, CallbackQuery):
        await event.answer()
    if question is None:
        await msg.answer(t(locale, "no_question"))
        return
    options = question.payload.get("options", [])
    labels = [str(o.get("text", "")) for o in options]
    await msg.answer(question.stem, reply_markup=keyboards.question_keyboard(question.id, labels))


async def _pick_daily(session: AsyncSession, language: str) -> bank.QuestionDTO | None:
    subjects = await catalog.list_subjects(session)
    if not subjects:
        return None
    # Rotate the subject by Tashkent-independent ordinal day; any stable rotation is fine.
    start = datetime.now(UTC).toordinal() % len(subjects)
    for offset in range(len(subjects)):
        subject = subjects[(start + offset) % len(subjects)]
        picked = await bank.pick_questions(session, subject_id=subject.id, language=language, n=5)
        for q in picked:
            if q.kind == "single_choice" and q.payload.get("options"):
                return q
    return None


@router.callback_query(F.data.startswith(f"{keyboards.PREFIX_QUESTION}:"))
async def on_answer(cb: CallbackQuery) -> None:
    if not isinstance(cb.message, Message) or cb.data is None:
        return await cb.answer()
    parsed = keyboards.parse_question_data(cb.data)
    async with get_sessionmaker()() as session:
        locale = await _locale(session, cb.message.chat.id, cb.from_user.language_code)
        if parsed is None:
            return await cb.answer(t(locale, "expired"), show_alert=True)
        qid, idx = parsed
        found = await bank.get_questions(session, [qid])
        options = found[0].payload.get("options", []) if found else []
        if not found or not 0 <= idx < len(options):
            return await cb.answer(t(locale, "expired"), show_alert=True)
        result = await bank.grade(session, qid, {"choice": options[idx]["id"]})
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(t(locale, "correct" if result.correct else "wrong"))
    await cb.answer()


__all__ = ["DEFAULT_LOCALE", "router"]
