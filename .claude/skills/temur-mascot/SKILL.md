---
name: temur-mascot
description: Use for generating, regenerating or adding Temur mascot poses (brand webp/png), or any image that must contain the Temur fox; not for icons or UI that code can render.
---

# Temur mascot

Temur is DTM AI's corsac fox. The look sits between Duolingo's Duo (flat geometric vector, bold silhouette, huge Duo eyes) and the corsac design in `../dtmai-design/` (read-only). He must NOT look plush.

## Reference
- Master sheet: `.claude/skills/temur-mascot/temur-reference-sheet.webp` (1024x1024, front head). Always pass it as `input` (Image 1) to every generation.
- Original line art (ear shape, muzzle, cheek spikes): `../dtmai-design/straight.png` (+ left/right/top/left bottom/right bottom). Read-only.

## Character spec
- Silhouette: tall narrow pointed ears (about 1.2x head height), head wider than tall, 3 sharp angular cheek spikes per side, narrow muzzle, bushy tail with cream tip. Body in poses: small, 2 to 2.5 heads tall, short limbs, paws with pink pads.
- Palette: fur `#C9C29A`; shade (ear backs, head-top wedge, tail) `#B3AA82`; cream muzzle/cheeks/inner ears/chest/tail tip `#F6EFD6`; stroke `#8F8760` (thin, uniform, same hue); nose and pupils `#3B2F1E`/`#2A1E14`; tongue `#FF8C9A`, mouth `#8E3B35`; paw pads pink.
- Eyes (Duo eyes): perfectly round pure white circles, wide apart, about 25% of face width each; pupil big dark round about 45% of eye width, slightly up/forward, one small white highlight dot upper right. No eyelids, no brows, never angry/narrowed (sleep = closed curves, sad = tilted pupils only).
- Doppi: small flat-top skullcap between the ears, brand `#100FA0`, zigzag band `#AFF50B`, slightly darker top ellipse. Always present, never altered.
- Style: cel-flat, max 2 tones per area, no gradients, no fur texture, no soft shading, no glow. Props are flat too (gold `#FFC800`, flame `#FF9600`).
- Do: crisp geometric shapes, same proportions every pose, props in brand colours. Don't: plush/airbrushed fur, extra clothing (no vest), eyebrows, realistic anatomy, text in the image, changing doppi colours.

## Base prompt (prefix for every pose)
```
Image 1 is the master character Temur (flat geometric Duolingo-Duo-style corsac fox: tall pointed cream-inner ears, sandy #C9C29A fur, cream muzzle and angular cheek spikes, huge round white eyes with large dark pupils and highlight dots, small dark nose, blue #100FA0 doppi with lime #AFF50B zigzag). Same character exactly, no clothing besides the doppi, NO eyebrows, NO angry or narrowed eyes. Full-body, same flat geometric style, thin darker same-hue stroke, no gradients, no fur texture, not plush. Pose: <SUFFIX>. Solid pure white background.
```
Head views replace "Full-body" with "head only" and use the suffixes marked (head).

## Pose suffixes (file `temur-<name>.webp`)
- straight (head): front view, open smile (this is the master).
- left / right (head): 3/4 turn to viewer's left / right. top (head): tilted down, doppi prominent, eyes up at viewer. left-bottom / right-bottom (head): turned left / right, chin lowered, looking down.
- celebrate: flying/jumping, both arms raised, mouth wide open, flat confetti.
- sad: sitting slumped, small tear, small frown, holding a small grey broken heart (cute, not scary).
- thinking: paw on chin, eyes up, flat white thought bubble with blue question mark.
- streak: flying, holding a big flat orange flame with yellow core.
- sleep: curled up, closed-eye curves, peaceful smile, flat "z" letters.
- trophy: flying, arms up holding a flat gold trophy overhead.
- premium: flying, flat gold crown above the doppi, small gold stars.
- wave: standing, one paw waving hello.
- reading: sitting with an open blue book in both paws.
- calendar: standing with a flat calendar planner (day grid, lime check) and a pencil.
- rush: dashing leaning forward, ears swept back, yellow speed lines and lightning bolt, excited smile (add "NO eyebrows, cheerful" or he turns angry).
- chat: standing, talking, paw raised, white speech bubble with blue outline and three dots (add "NO vest").
- point: standing, one arm pointing to viewer's right, other paw on hip, confident smile.
- lock: standing hugging a big flat gold closed padlock, playful smile (Pro locked).
- question: head tilted, paw raised, big lime question mark with blue outline floating above (FAQ).

## Tool workflow
1. `generate_image` (model openai-codex gpt-image-2, default role), `input: [master reference]`, `aspect_ratio` 1:1 for heads and wide poses, 2:3 for tall standing/flying poses. One image per call, at most 3 retries per pose; inspect each result with `read` (eyes, doppi, brows, vest, stray text).
2. Remove the white background: `magick raw.webp -bordercolor white -border 1 -fuzz 4% -fill none -draw 'color 0,0 floodfill' -shave 1x1 -trim +repage pose.png`.
3. Export web: `magick pose.png -resize x720 -define webp:alpha-quality=100 -quality 82 apps/web/public/brand/temur-<name>.webp`.
4. Export mobile: `magick pose.png -resize x720 PNG32:apps/mobile/assets/brand/<name_with_underscores>.png`.

## Output specs
Transparent-background WebP (q82), 720 px tall, width follows the trimmed art (about 470 to 720 px). Squares/heads about 680x720.

## Naming and mirroring
- Web: `apps/web/public/brand/temur-<kebab-name>.webp`.
- Mobile: `apps/mobile/assets/brand/<snake_name>.png` (no `temur_` prefix, e.g. `left_bottom.png`).
- `apps/admin/public` has no Temur copies; do not add unless admin starts using them. `apps/web/out` is a build artefact.
- Update `apps/web/public/brand/README.md` when adding poses. Alt text: "Temur the fox mascot <pose description>".
- Never overwrite poses without regenerating the whole set so identity stays consistent.

## Scenes (use the base prompt prefix, replace "Pose" with "Scene")
Input images: master + the previous version of the scene for composition. Generate 4:3 (hero 3:2), remove white (step 2), then trim and fit.
- `hero-landing.png` (1599x900 transparent PNG, art right-aligned at 880 px tall, left third empty): Temur flying upward, one paw holding an open blue book with lime bookmark, other raising a blue smartphone with lime check; gold coins, yellow sparkles, small flat lyceum building (blue roof, green bushes) bottom right.
- `illus-path.webp` (800x600): Temur walking on the left, winding S-shaped lime #AFF50B path with 8 empty white round nodes with lime rings rising to the top right.
- `illus-lyceum-dream.webp` (800x600): Temur on the left pinning a photo of a lyceum building with a red pushpin onto a wooden-framed cork board; no vest or clothing.
- `illus-register.webp` (800x600): Temur front, hugging a stack of five flat books (red, orange, yellow, green, purple).
- `illus-mocks.webp` (800x600): Temur front, left paw holds a crisp bright pure-white exam sheet with bold dark-grey #3C3C3C lines, bold lime check marks, thick blue #100FA0 header bar and dark outline (high contrast, not washed out); right paw holds a bold blue #100FA0 stopwatch.
- `temur-trophy.webp`: add "trophy floats a clear head-height above the doppi, normal short bent arms". If white remains enclosed between arms, cup and head, clear it with `magick in.png -fuzz 6% -fill none -draw "color X,Y floodfill"` at a seed inside the gap.
- Scenes: fit with `magick s.png -trim +repage -resize 800x600 -background none -gravity center -extent 800x600 -define webp:alpha-quality=100 -quality 82 out.webp`; hero with `-resize x880 -gravity east -extent 1599x900`.
- `app-icon-1024.png` (1024 opaque; mirror to `apps/mobile/assets/brand/app_icon.png`): built with ImageMagick, not generated: `#100FA0` canvas, `#AFF50B` circle r=414 at centre, white circle r=384, `straight` head 660 px wide centred (+0+10). No other launcher icons exist in `apps/mobile` yet.
