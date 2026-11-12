---
name: i18n
description: Use when adding or changing user-visible text or locales.
---

# i18n
- Locales: `uz-Latn` (default), `uz-Cyrl`, `ru`, `en`. Messages in `packages/i18n`; keys must exist in all four (parity test).
- Backend user-facing strings (emails, bot, notifications) are keyed per locale too; users have a `locale`.
- Content from DB (subjects, topics, questions) carries translations per locale; never hardcode names.
- Uzbek Cyrillic is a transliteration target of Latin: keep terminology consistent; numbers/dates via Intl with the locale.
