# Brand assets

Mascot: **Temur**, Uzbek corsac fox in Duolingo-style flat vector art: no outlines, chunky rounded shapes, 2-3 flat tones, big simple eyes, grey-sand fur (#C8BFA6 / #B3A98C), cream muzzle and inner ears (#F6EFD6), doppa in brand blue #100FA0 with a #AFF50B zigzag band. All files derive from the `straight` master (reference drawings live in dtmai-design/).

> Mascot poses are shipped as `temur-<mood>.webp` (720px max, q82) for web weight; the PNG masters are not kept in the repo.

## Head views (transparent)
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

## Illustrations (800x600 transparent WebP, card slots)
- `illus-path.webp` Temur on a winding path of lesson nodes; `illus-lyceum-dream.webp` pinning a lyceum photo on a wall; `illus-mocks.webp` exam sheet and timer; `illus-register.webp` stack of subject books. Alt: "Temur the fox mascot <walking a learning path|pinning a lyceum photo|holding an exam sheet and timer|holding subject books>".

## Prompts (reproducibility)
Model: openai-codex gpt-image-2. Master `straight` (input: dtmai-design/straight.png as reference): "Temur, a corsac fox mascot head only, front view, redrawn in the exact style of Duolingo character art: flat vector shapes, NO outlines, chunky rounded geometry, 2-3 flat tones per area with one soft highlight/shadow shape, big simple oval eyes with white highlight dot, tiny black nose, simple smile, very few details. Grey-sand fur (#C8BFA6 with #B3A98C shade), cream muzzle and inner ears (#F6EFD6). Small doppa on top, solid #100FA0 with a simple #AFF50B zigzag band. Solid pure white background."
Every other asset: master as Image 1, "Image 1 is the master character Temur. <scene>. Identical flat vector style as Image 1, no outlines. Solid pure white background." Scenes: left/right = head 3/4 turn; top = head tilted down; left-bottom/right-bottom = turned with chin lowered; celebrate = full body flying, arms raised, confetti; sad = sitting slumped, teary, grey broken heart; thinking = paw on chin, question bubble; streak = flying holding flat orange flame; sleep = curled up, closed eyes, "z"s; trophy = flying with gold trophy overhead; premium = flying with gold crown and stars; wave = waving paw; hero = right side Temur flying with open book, gold coins/stars and phone with lime check, left 45% empty (16:9); illus-path = Temur on winding path of lime/white nodes; illus-lyceum-dream = pinning framed lyceum picture to a board; illus-mocks = exam sheet and stopwatch; illus-register = hugging five subject books.
Post-processing: white background removed by ImageMagick flood fill (fuzz 2%), trimmed, resized (poses 720px tall WebP q82; illus 800x600; hero 1600x900 right-aligned; app icon = master head on #100FA0, 1024). Mobile copies of poses are in apps/mobile/assets/brand/*.png.

## Icon set (256x256 transparent PNG, hand-authored flat SVG rasterised, same palette as Temur)
`icon-streak`, `icon-xp`, `icon-gem`, `icon-heart`, `icon-lesson`, `icon-mock`, `icon-lyceum`, `icon-trophy`, `icon-lock`, `icon-check` (mobile copies: `apps/mobile/assets/brand/icon_*.png`). `icon-league.png` and `icon-review.png` are legacy 512px icons kept untouched. Decorative (`alt=""`) beside labels.

## App icon
`app-icon-1024.png`: Temur head on a white circular badge with a #AFF50B ring over #100FA0, so the doppa stays visible; copy at `apps/mobile/assets/brand/app_icon.png`.
