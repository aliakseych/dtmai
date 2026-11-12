---
name: content-pipeline
description: Use for question ingestion, AI labeling/verification, generation runs and admin review.
---

# Content pipeline
- Sources: files in `./data` (read-only) and admin uploads (images/PDF) -> AI extraction -> `bank.Question` status `draft`.
- Labeling: several models (OpenRouter) solve independently; judge agreement -> `auto_agreed`, disagreement -> `escalated`, unresolved -> `needs_human`; humans -> `verified`.
- Blind audit sampling and bulk approve above a confidence threshold; keep metrics.
- Subjects/topics/question types are DB data from catalog; generation rules drive prompts. Never hardcode.
- Official previous-year papers keep `source=official_year` + year.
