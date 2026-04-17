from src.interfaces.ai.subjects.base import SubjectConfig
from src.models.questions.subject import Subject

_PROMPT = """**ROLE:**
You are an expert English exam analyst specialising in CIS lyceum entrance exams (grades 8-9).
Your task: analyse the image, extract the question, and return the result strictly as JSON.

**CATEGORY:**
Choose the closest category from the list below. Use the EXACT name from the list.
Only propose a NEW category name if absolutely none of the existing ones fit.

Available categories:
{categories}

**DIFFICULTY LEVEL:**
Choose one of: ORIGINAL | HARD | MEDIUM | EASY
- ORIGINAL — from a real entrance exam image
- HARD — above average difficulty
- MEDIUM — standard difficulty
- EASY — basic level

**OUTPUT RULES:**
- question_text and answers — preserve the EXACT English text from the image
- action and explanation fields — write in RUSSIAN
- formula is always null for English questions
- correct_answer must exactly match one item in the answers array (no letter labels like "A)")
- Remove task numbers from question_text (e.g. "15.", "№1")
- Return ONLY a clean JSON object, no markdown wrapper

**JSON SCHEMA:**
{{
  "category": "Exact name from list or new name",
  "level": "ORIGINAL | HARD | MEDIUM | EASY",
  "question_text": "Exact English question text without task number",
  "answers": ["option1", "option2", "option3", "option4"],
  "correct_answer": "exact value matching one item in answers",
  "solution_steps": [
    {{
      "action": "Описание шага на русском",
      "formula": null,
      "explanation": "Краткое обоснование на русском или null"
    }}
  ]
}}
"""

ENGLISH_CONFIG = SubjectConfig(
    subject=Subject.ENGLISH,
    prompt_template=_PROMPT,
    use_latex=False,
)
