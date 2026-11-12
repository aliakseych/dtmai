# UI rules (web, admin, mobile)

Every rule is checkable in review. Source of truth for values: `packages/ui/src/tokens.css`; for atoms: `packages/ui/src/index.ts`.

## 1. Tokens and colour
1.1 Only token classes. No hex, `rgb()`, or Tailwind palette colours (`text-gray-500`, `bg-emerald-100`) in `apps/*` or `packages/ui` components.
- Do: `text-ink-soft`, `border-line`, `bg-brand-soft`, `stroke="var(--color-line)"`
- Don't: `text-[#afafaf]`, `bg-[#58cc02]`, `text-gray-500`

1.2 Palette and meaning:

| Token | Use |
|---|---|
| `brand` / `brand-deep` / `brand-soft` | primary actions, selected state, links, progress / pressed edge / tinted background |
| `accent` / `accent-deep` / `accent-soft` / `accent-ink` | highlight, Pro/"super", rewards / edge / tint / accent-coloured text on white |
| `ink` / `ink-soft` / `ink-mute` | text / secondary text / disabled and placeholder |
| `line` / `line-deep` / `snow` / `white` | borders / pressed edge of white buttons / page tint and hover / surfaces |
| `red` / `red-deep` / `red-soft` / `red-ink` | errors, hearts, destructive only |
| `correct` / `correct-deep` | correct-answer feedback only |

1.3 `accent` is a background, never text on white (contrast). Text on `bg-accent` is `text-ink`; accent-coloured text is `text-accent-ink`.
1.4 `green*`, `blue*`, `gold*`, `orange*` tokens are deprecated aliases. Never use them in new code.
1.5 Exceptions: `flags.tsx` (national flags), `themeColor` in `app/layout.tsx`.

## 2. Atoms (`@dtmai/ui`) - use these, not ad-hoc markup

| Need | Atom |
|---|---|
| Button / link that looks like a button | `Button` / `buttonClass(variant)` on `Link` |
| Surface | `Card` (`pad`, `interactive`) / `cardClass()` on `Link`, `li`, `button` |
| Status pill, chip, count | `Badge` |
| Nothing-here state | `EmptyState` |
| Loading / error / empty around a query | `AsyncView` (web) |
| Page h1 | `PageTitle` |
| Icon | `Icon`; status glyphs `FlameIcon`, `HeartIcon`, `GemIcon`, `XpIcon`, `StarIcon`, `LockIcon`, `CheckIcon`, `CrossIcon` |
| Fox | `Mascot` |
| Segmented switch | `Tabs` |
| Overlays | `Sheet` (mobile bottom), `Modal` (confirm), `Toast` |
| Progress | `ProgressBar` |
| Stats in header | `XpStat`, `GemsStat`, `StreakFlame`, `Stat` |

2.1 `cn()` is a plain join, not tailwind-merge. Do not pass a class that conflicts with an atom's own class (`<Card className="p-3">` loses to `p-5`); use the atom's prop (`pad="sm"`, `pad="none"`).
2.2 If an atom is missing a variant, add the variant to the atom; do not fork the markup in an app.

## 3. Icons
3.1 One system: `<Icon name="..." size={...} />` - 24 grid, 2px stroke, round caps, `currentColor`, no fill. Add new glyphs to `packages/ui/src/components/icons.tsx` in the same style.
3.2 Sizes are only 16, 20, 24, 28, 32:

| Size | Where |
|---|---|
| 16 | inside `Badge`, inline with `text-xs`/`text-sm` |
| 20 | inside buttons, list-row chevrons, inline with body text |
| 24 | default; bottom tab bar, More sheet, icon-only buttons |
| 28 | sidebar nav, icon tiles (`size-12`/`size-14 rounded-2xl bg-brand-soft text-brand`) |
| 32 | large placeholders |

3.3 Colour comes from the parent's text colour. Do not set `fill`/`stroke` on an `Icon`.
3.4 Filled status glyphs are only for game stats (streak, hearts, gems, XP), path nodes and answer feedback. Never for navigation or actions.
3.5 Forbidden as icons: emoji, text glyphs (`×`, `←`, `✓`, `☰`, `⚑`, `‹`), PNG/`<img>` icons, inline one-off `<svg>` in app code, coloured squares.
- Do: `<button aria-label={t("common.close")} className="grid size-10 place-items-center"><Icon name="close" /></button>`
- Don't: `<button className="text-3xl">×</button>`

3.6 Icons are decorative (`aria-hidden`) by default. An icon-only control needs `aria-label` on the control (or `label` on the `Icon`).
3.7 Fixed mapping - plan task kinds: lesson `learn`, drill `practice`, review `review`, mock `mocks`, rush `bolt`. Nav icons are declared in `apps/web/src/components/layout/nav.ts` as `IconName`.

## 4. Cards
4.1 Spec: `rounded-card` (16px), `border-2 border-line`, `bg-white`, padding `p-5` (`pad="md"`, default) or `p-4` (`pad="sm"`, dense lists/KPIs); `pad="none"` for lists and tables that own their padding.
4.2 Tappable card: `interactive` -> `border-b-4` + `hover:bg-snow`. Static cards never have the thick bottom border.
4.3 Selected card: `border-brand bg-brand-soft`. Highlighted/Pro card: `border-accent-deep bg-accent-soft`.
4.4 No blur shadows (`shadow-sm/md/lg`) on cards, tooltips, charts. Only floating menus/popovers may use `shadow-xl`.
4.5 Do not nest a `Card` in a `Card`; use `bg-snow rounded-2xl` for an inner block.
- Do: `<Card pad="sm" className="flex items-center gap-4">`
- Don't: `<div className="rounded-card border-2 border-line bg-white p-4">`, `<div className="rounded-lg shadow-md">`

## 5. Buttons
5.1 Variants: `primary` (one per view, the main action), `secondary` (white, alternative), `ghost` (tertiary, text-like), `danger` (destructive only), `super` (accent; Pro/upgrade only).
5.2 Spec: `rounded-2xl`, `px-5 py-3`, `text-[15px] font-extrabold uppercase`, 4px bottom edge, press translates 4px. Do not rebuild this with raw classes.
5.3 Links that act as buttons: `<Link className={buttonClass("primary")}>`. Full width on mobile forms: `block`.
5.4 Hit area >= 40x40px (`size-10`) for icon-only buttons; >= 44px tall for primary actions.
5.5 Label is a verb from i18n; no trailing glyph arrows.

## 6. Badges and chips
6.1 `Badge` spec: `rounded-full border-2 px-2.5 py-0.5 text-xs font-extrabold`, optional leading 16px `Icon`.
6.2 Tones: `neutral` (meta info), `brand` (done/active/selected), `accent` (highlight, verified, Pro, warning-attention), `danger` (error/overdue), `outline` (quiet counters, "none").
6.3 No hand-rolled pills (`rounded-full bg-... px-2 text-xs`). No `rounded-lg` chips.
- Do: `<Badge tone="brand"><Icon name="check" size={16} />{t("quests.done")}</Badge>`
- Don't: `<span className="rounded-full bg-green-100 px-3 py-1">✓ Done</span>`

## 7. Type and spacing
7.1 Heading scale: page h1 = `PageTitle` (`text-3xl`), one per page; section h2 `text-xl`; card title `text-lg font-extrabold`; overline `text-sm font-extrabold uppercase text-ink-soft`; landing section h2 `text-3xl`. Body `text-base`, meta `text-sm text-ink-soft`. Nothing below `text-xs`.
7.2 Weights: 700 (`font-bold`) body emphasis, 800 (`font-extrabold`) headings, buttons, badges.
7.3 Spacing steps: `gap-1/2/3/4/6/8`. Between page sections `gap-6`; inside a card `gap-3` or `gap-4`; list of cards `gap-3`.
7.4 Radii: `rounded-card` surfaces, `rounded-2xl` buttons/tiles/inputs, `rounded-xl` small controls, `rounded-full` badges/avatars. No `rounded`, `rounded-md`, `rounded-lg`.

## 8. Layout at 375px
8.1 Every screen works at 375x667 with no horizontal scroll. Page padding `px-4`; content column max `max-w-2xl` (reading) or the shell width.
8.2 Flex rows with text: text container has `min-w-0` and `truncate` or wraps; icons/badges have `shrink-0`.
8.3 Grids start at 1 column (2 for KPI tiles) and widen at `sm:`/`lg:`. No fixed pixel widths above 320px.
8.4 Bottom tab bar has 5 slots max (4 destinations + More); content gets bottom padding for the bar and safe area.
8.5 Sticky footers (lesson CHECK bar) respect `env(safe-area-inset-bottom)`.
8.6 Overlays: `Sheet` on mobile, `Modal` for confirmations; never a custom fixed div.

## 9. Empty, loading, error states
9.1 Data views go through `AsyncView`: loading = mascot `thinking` + `common.loading`; error = mascot `sad` + message + `common.retry` button; offline = `sleep` + `common.offline`.
9.2 Empty = `EmptyState` with a title, optional body, and one action if the user can fix it. Inside a list/card where a mascot is too heavy: `<EmptyState compact title=... />`.
9.3 Never render a blank area, a bare "No data" string, or a spinner without text.
- Do: `<EmptyState mood="calendar" title={t("plan.empty.title")} body={t("plan.empty.body")} action={<Link className={buttonClass("primary")} href="/plan/setup/">{t("plan.generate")}</Link>} />`
- Don't: `{items.length === 0 && <p>Nothing yet</p>}`

## 10. Mascot poses
10.1 Always `<Mascot mood="..." />`; never `<img src="/brand/temur-...">`. Decorative -> `alt=""`; the only content of a block -> `alt={t("mascot.alt")}`.
10.2 One mascot per viewport. Not inside list rows, badges or buttons.
10.3 Mapping:

| Context | `mood` |
|---|---|
| Loading, AI generating an answer | `thinking` |
| Error, failed attempt, out of hearts | `sad` |
| Offline, rest day | `sleep` |
| Generic empty state | `point` |
| Theory / reading / explanations | `reading` |
| Planner: no plan, wizard, generating | `calendar` |
| Rush mode | `rush` |
| Ask Temur chat | `chat` |
| Locked Pro feature | `lock` |
| Premium page / upsell banner | `premium` |
| FAQ / help | `question` |
| Success, lesson complete, plan ready | `celebrate` |
| Streak | `streak` |
| Leagues / results podium | `trophy` |
| Greeting, landing hero, auth | `wave` |
| Directional/decorative only | `straight`, `left`, `right`, `top`, `left-bottom`, `right-bottom` |

10.4 Sizes: 72 (inline in a card), 96-120 (empty/loading states), 140-180 (hero, result screens).

## 11. Motion
11.1 Library: `motion/react`. Every component with JS animation calls `useReducedMotion()` and, when reduced, uses `initial={false}` / no transforms / `duration: 0`.
11.2 CSS helpers (`sheet-in`, `pop-in`, `menu-in`, `fade-up`, `bob`) are already disabled under `prefers-reduced-motion`; prefer them for simple entrances.
11.3 Durations: 120-200ms for UI transitions, <= 600ms for celebration. Springs only for rewards/checkmarks. Animate `transform` and `opacity` only.
11.4 No looping animation except the mascot `bob` and loading indicators.
- Do: `initial={reduce ? false : { opacity: 0, x: 24 }}`
- Don't: `initial={{ opacity: 0, x: 24 }}` without a reduced-motion branch

## 12. Accessibility
12.1 Icon-only controls have `aria-label` from i18n. Never a glyph as the label (`aria-label="+"`).
12.2 Interactive elements are `button`/`a`/`Link`; no `div onClick`. Custom radios/tabs carry `role` + `aria-checked`/`aria-selected`.
12.3 Focus ring is the global brand ring; never `outline-none` without a replacement.
12.4 State is never colour-only: add an icon or text (check, lock, flag, label).
12.5 Text contrast >= 4.5:1: body text is `ink` or `ink-soft`; `ink-mute` only for disabled/placeholder.
12.6 One `h1` per page; headings do not skip levels. Live results use `role="status"` / `role="alert"`.

## 13. i18n
13.1 All visible text and all `aria-label`/`alt`/`title` strings come from `t()`. No literals, including symbols used as words.
13.2 Keys exist in all four locales: `uz-Latn` (default), `uz-Cyrl`, `ru`, `en`. Reuse `common.*` (`loading`, `error`, `retry`, `empty`, `close`, `back`, `continue`) before adding keys.
13.3 No string concatenation of sentences; use params (`t("plan.daysLeft", { n })`).
13.4 Layouts tolerate 40% longer text (Russian, Uzbek Cyrillic): no fixed-width text buttons, allow wrap or `truncate` with `min-w-0`.
13.5 Subjects, topics, question types, plans, lyceums are API data: never hardcoded labels, and icons for them are decorative only.
13.6 uz-Latn typography: `o‘`/`g‘` use U+2018; other apostrophes use U+02BC.

## Review checklist
- [ ] No hex / palette colours / deprecated colour tokens
- [ ] No emoji, glyph, PNG or inline-svg icons; `Icon` sizes from {16, 20, 24, 28, 32}
- [ ] Surfaces are `Card`, pills are `Badge`, buttons are `Button`/`buttonClass`
- [ ] No blur shadow on cards; only tappable cards have `border-b-4`
- [ ] Empty/loading/error states present, mascot pose per section 10
- [ ] Works at 375px, no horizontal scroll, `min-w-0` on text in rows
- [ ] `useReducedMotion` on every `motion` component
- [ ] Icon-only controls labelled; all strings via i18n in 4 locales
