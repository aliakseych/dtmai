# Brand assets

Mascot: **Temur**, Uzbek corsac fox, redesigned as a flat geometric Duo-style character (crisp silhouette, thin same-hue stroke, 2 flat tones per area, not plush). Full spec, prompts and workflow: `.claude/skills/temur-mascot/SKILL.md` (reference sheet there). New poses: `temur-reading`, `temur-calendar`, `temur-rush`, `temur-chat`, `temur-point`, `temur-lock`, `temur-question`.

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
Model: openai-codex gpt-image-2. Master `straight` (inputs: dtmai-design/straight.png for ear shape/palette + a Duolingo Duo eye reference): "Temur, a friendly corsac fox mascot, head only, front view, in the exact style of Duolingo's Duo character art. Eyes are HUGE perfectly round pure white circles taking up a large share of the face, set wide apart, each with a large dark brown-black round pupil (about 45% of eye width, looking slightly up-and-forward) and a small white highlight dot; NO eyebrows, no eyelids, no angry or narrowed shape: cheerful, wide-eyed, innocent. Friendly wide open-mouth smile with a soft pink tongue under a tiny rounded black nose. Soft rounded flat vector, NO outlines, chunky rounded geometry, 2-3 flat tones per area. Grey-sand fur #C8BFA6 with #B3A98C shade, cream muzzle and inner ears #F6EFD6, large pointed ears. Small doppa hat on top, solid #100FA0 with a simple #AFF50B zigzag band. Solid pure white background."
Every other asset: master as Image 1, "Image 1 is the master character Temur. <scene>. Keep huge round white eyes with large dark pupils and white highlight dots, friendly smile, same fur and doppa. Identical flat vector style as Image 1, no outlines. Solid pure white background." Scenes: left/right = head only, 3/4 turn; top = head tilted down; left-bottom/right-bottom = turned with chin lowered, looking down; celebrate = full body flying, arms raised, confetti; sad = sitting slumped, small tear, small frown, grey broken heart (cute, not scary); thinking = paw on chin, question bubble; streak = flying holding flat orange flame; sleep = curled up, closed eyes as soft curves, "z"s; trophy = flying with gold trophy overhead; premium = flying with gold crown and stars; wave = standing, waving paw; hero (16:9) = right side Temur flying with open book, gold coins/stars, phone with lime check and small lyceum building, left 45% empty; illus-path = Temur on winding path of lime/white nodes; illus-lyceum-dream = pinning framed lyceum picture to a board; illus-mocks = exam sheet and stopwatch; illus-register = hugging a stack of five subject books (4:3).
Post-processing: white background removed by ImageMagick flood fill from the four corners (fuzz 3%), trimmed, resized (poses 720px tall WebP q82 via cwebp; illus 800x600 centered; hero 1600x900 right-aligned, not trimmed; app icon = master head 640px on a white circle with #AFF50B ring over #100FA0, 1024). Mobile copies of poses are in apps/mobile/assets/brand/*.png (underscored names).

## Icon set (256x256 transparent PNG, hand-authored flat SVG rasterised, same palette as Temur)
`icon-streak`, `icon-xp`, `icon-gem`, `icon-heart`, `icon-lesson`, `icon-mock`, `icon-lyceum`, `icon-trophy`, `icon-lock`, `icon-check` (mobile copies: `apps/mobile/assets/brand/icon_*.png`). `icon-league.png` and `icon-review.png` are legacy 512px icons kept untouched. Decorative (`alt=""`) beside labels.

## App icon
`app-icon-1024.png`: Temur head on a white circular badge with a #AFF50B ring over #100FA0, so the doppa stays visible; copy at `apps/mobile/assets/brand/app_icon.png`.
