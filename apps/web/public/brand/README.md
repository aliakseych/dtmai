# Brand assets

Mascot: **Temur**, Uzbek corsac fox (flat vector, dark navy outline #1b1b2e, grey-sand fur, cream inner ears, black ear and tail tips, doppa in brand blue #100FA0 with white pattern and lime #AFF50B stitching). All files derive from the `straight` master.

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

## Illustrations (800x600 transparent WebP, card slots)
- `illus-path.webp` Temur on a winding path of lesson nodes; `illus-lyceum-dream.webp` pinning a lyceum photo on a wall; `illus-mocks.webp` exam sheet and timer; `illus-register.webp` stack of subject books. Alt: "Temur the fox mascot <walking a learning path|pinning a lyceum photo|holding an exam sheet and timer|holding subject books>".

## Prompts (reproducibility)
Model: openai-codex gpt-image-2. Master `straight`: "Temur, friendly corsac fox mascot, head only, front view, big upright ears with cream inner ear and black tips, grey-sand fur (#C8BFA6), white cheeks, big glossy dark eyes, black nose, gentle smile, rosy cheeks, Uzbek doppa in #100FA0 with white pattern and #AFF50B accents. Duolingo-quality clean flat vector, bold dark outline (#1b1b2e), no gradients/shadows, solid white background." Every other asset: master passed as Image 1, "Image 1 is the master character Temur. <pose/scene description>. identical flat vector style as Image 1, solid pure white background". Poses: left/right 3/4 head turns, top (tilted down), left-bottom/right-bottom (turned + chin lowered); full-body celebrate, sad (broken heart), thinking (lightbulb), streak (flame), sleep (curled, zzz), trophy, premium (crown, stars), wave; hero (books + lyceum building, right-aligned, left empty); illustrations as listed above. White background removed with ImageMagick flood fill from the corner (`-fuzz 9%`), trimmed, resized (heads/poses max 720px WebP q82; illus 800x600 canvas). App icon: `straight` on #100FA0 composited with ImageMagick.
