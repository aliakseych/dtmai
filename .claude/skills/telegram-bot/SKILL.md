---
name: telegram-bot
description: Use for the Telegram bot, webhook, Mini App auth, Login Widget or reminders.
---

# Telegram
- aiogram, webhook at `/tg/webhook` on api.dtm-ai.uz, secret via `X-Telegram-Bot-Api-Secret-Token` (`TELEGRAM_WEBHOOK_SECRET`).
- Mini App auth: client sends `initData`; verify HMAC (key `"WebAppData"`, msg = bot token), check `auth_date` age. Login Widget: key = sha256(bot token). Code: `identity/domain/telegram.py`.
- `/start` deep link logs in / links accounts; menu button opens `https://app.dtm-ai.uz/tma`.
- Reminders go through the `notify` module, scheduled by taskiq scheduler. Set webhook per `deploy/DEPLOY.md`.
