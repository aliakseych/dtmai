---
name: ui-ux
description: Use when building or styling web, admin, or mobile UI.
---

# UI/UX (Duolingo-flat, DTM AI brand)
**Read [UI-RULES.md](UI-RULES.md) before touching UI. It is the checkable rule list; this file is the summary.**

- Font Nunito 700-800. Colours: brand `#100FA0`, accent `#AFF50B`, otherwise black/white/greys; red only for errors/hearts. Use token classes (`bg-brand`, `text-ink-soft`), never hexes.
- Chunky buttons: 4px darker bottom edge, press = translateY(4px). Cards: 16px radius, 2px `line` border, tappable cards add a 4px bottom border. Flat, no blur shadows.
- Atoms live in `packages/ui` (`Button`, `Card`, `Badge`, `EmptyState`, `Icon`, `Mascot`, `Tabs`, `Sheet`, `Modal`, ...). Compose them; do not re-create them with ad-hoc markup.
- Icons: `<Icon name size>` only. No emoji, text glyphs or PNG icons.
- Mascot Temur (corsac fox): `apps/web/public/brand/temur-<pose>.webp` via `<Mascot mood>`; pose mapping in UI-RULES.md.
- Lesson flow: CHECK -> feedback sheet (correct/red) -> CONTINUE.
- Mobile mirrors the tokens. Accessible contrast and keyboard support; all text via i18n.
