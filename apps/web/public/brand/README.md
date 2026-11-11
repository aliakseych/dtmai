# Brand assets

Mascot: **Temur**, Uzbek corsac fox (flat style, dark-olive outline, sand fur, cream ears, teal doppa with yellow zigzag).

> Mascot poses are shipped as `temur-<mood>.webp` (720px max, q82) for web weight; the PNG masters are not kept in the repo.

## Originals (2048px, off-white background; source of truth for the mascot)
- `temur-straight.webp`, `temur-left.webp`, `temur-right.webp`, `temur-top.webp`, `temur-left-bottom.webp`, `temur-right-bottom.webp`: head views for avatars, loaders, favicons.

## Mascot poses (transparent PNG, ~1024px tall; AI-generated)
- `temur-celebrate.webp`: lesson complete, correct answer streaks, confetti.
- `temur-sad.webp`: out of hearts, failed lesson, error states.
- `temur-thinking.webp`: hints, AI tutor, empty states, loading.
- `temur-streak.webp`: streak milestones, streak reminders (holds flame).
- `temur-sleep.webp`: inactivity, offline, streak-at-risk notifications.
- `temur-trophy.webp`: league promotion, mock results, achievements.
- `temur-premium.webp`: Premium paywall and pricing (crown, stars).
- `temur-wave.webp`: welcome, onboarding, login.

## Landing
- `hero-landing.png`: 1600x900 transparent hero, Temur with books and lyceum building; content space on the left.

## Icons (512x512 transparent PNG, hand-authored SVG rasterised; Duolingo palette)
- `icon-streak.png` flame, `icon-gem.png` gems, `icon-heart.png` hearts, `icon-xp.png` XP bolt, `icon-mock.png` mock exams, `icon-review.png` mistakes review, `icon-league.png` leagues shield, `icon-lyceum.png` lyceum explorer.

## App icon
- `app-icon-1024.png`: 1024x1024 opaque, Temur head on brand blue #100FA0 (mobile/PWA/Telegram bot).

## Alt text suggestions
Mascot poses: "Temur the fox mascot <celebrating|sad|thinking|holding a flame|sleeping|holding a trophy|wearing a crown|waving>". Icons are decorative (`alt=""`) when beside a label.

## Prompts (reproducibility)
Model: openai-codex gpt-image-2, input the `straight` original above. Style suffix: "Flat vector mascot matching Image 1 exactly: thick dark-olive (#5a4f1e) outline, sand fur (#c9c49a), cream inner ears (#faf3d6), teal doppa (#1a9a9a) with yellow zigzag (#d4d01c). No gradients, no shadows. Solid pure white background." White background removed with ImageMagick flood fill (`-fuzz 6%`).
