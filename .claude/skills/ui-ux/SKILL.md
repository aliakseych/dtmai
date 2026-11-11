---
name: ui-ux
description: Use when building or styling web, admin, or mobile UI.
---

# UI/UX (Duolingo-like)
- Font Nunito 700-800. Colors: green #58cc02 (3D bottom #58a700), blue #1cb0f6, text #4b4b4b, border #e5e5e5, red #ff4b4b, gold #ffc800, orange #ff9600, brand #100FA0.
- Chunky buttons: `border-bottom: 4px solid <darker>`, press = translateY(4px) and border 0. Cards: 16px radius, 2px #e5e5e5 border. Flat, no blur shadows.
- Mascot Temur (corsac fox): `apps/web/public/brand/`. Lesson flow: CHECK -> feedback sheet (green/red) -> CONTINUE.
- Shared tokens/atoms in `packages/ui`; mobile mirrors the tokens. Accessible contrast and keyboard support; all text via i18n.
