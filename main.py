from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

FRONTEND_DIR = BASE_DIR / "frontend"
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=30000)


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=300)
    count: int = Field(default=5, ge=1, le=10)


class PathRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=300)
    level: str = Field(default="Beginner", pattern="^(Beginner|Intermediate|Advanced)$")


app = FastAPI(
    title="EduGenie API",
    version="2.0.0",
    description="AI-powered educational assistant",
)

origins = [
    item.strip()
    for item in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if item.strip()
]

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def clean_text(value: str) -> str:
    return value.strip()


def fallback_answer(question: str) -> str:
    q = question.lower()
    if "largest ocean" in q:
        return (
            "The Pacific Ocean is the largest ocean on Earth. "
            "It covers more area than any other ocean."
        )
    if "pythagoras" in q or "pythagorean theorem" in q:
        return (
            "The Pythagorean theorem is used with right-angled triangles. "
            "It says a² + b² = c², where c is the hypotenuse. "
            "For example, if a = 3 and b = 4, then c = 5."
        )
    return (
        f"Here is a simple way to study your question: {question}\n\n"
        "1. Learn the main definition.\n"
        "2. Break the topic into smaller concepts.\n"
        "3. Study one worked example.\n"
        "4. Practice a few questions.\n"
        "5. Review the mistakes you make."
    )


def ai_generate(prompt: str) -> str | None:
    """Call Gemini when GEMINI_API_KEY is configured.

    Returning None intentionally activates deterministic local fallbacks,
    so the application remains usable without an API key.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        text = getattr(response, "text", None)
        return text.strip() if text else None
    except Exception:
        return None


def strip_code_fences(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def extract_json_array(value: str) -> list[dict[str, Any]] | None:
    """Extract a JSON array even if a model adds a short explanation."""
    cleaned = strip_code_fences(value)
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[[\s\S]*\]", cleaned)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        return None


def validate_quiz_questions(data: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    valid: list[dict[str, Any]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        question = item.get("question")
        options = item.get("options")
        answer = item.get("answer")
        explanation = item.get("explanation", "")

        if (
            not isinstance(question, str)
            or not isinstance(options, list)
            or len(options) != 4
            or not all(isinstance(x, str) for x in options)
            or not isinstance(answer, int)
            or answer not in range(4)
        ):
            continue

        valid.append(
            {
                "question": question.strip(),
                "options": [x.strip() for x in options],
                "answer": answer,
                "explanation": str(explanation).strip(),
            }
        )

        if len(valid) == count:
            break

    return valid


def fallback_quiz(topic: str, count: int) -> list[dict[str, Any]]:
    templates = [
        {
            "question": f"Which is a useful way to learn {topic}?",
            "options": [
                "Understand concepts and practice",
                "Skip examples",
                "Avoid revision",
                "Memorize without understanding",
            ],
            "answer": 0,
            "explanation": "Understanding concepts and practicing examples helps build lasting knowledge.",
        },
        {
            "question": f"What should you do first when starting {topic}?",
            "options": [
                "Learn the basic concepts and terms",
                "Start with the hardest problem",
                "Skip the introduction",
                "Avoid taking notes",
            ],
            "answer": 0,
            "explanation": "A strong foundation makes later concepts easier to understand.",
        },
        {
            "question": f"Which activity can help you improve at {topic}?",
            "options": [
                "Regular practice",
                "Never checking mistakes",
                "Studying only once",
                "Avoiding exercises",
            ],
            "answer": 0,
            "explanation": "Regular practice and reviewing mistakes are useful learning habits.",
        },
        {
            "question": f"How can you check your understanding of {topic}?",
            "options": [
                "Explain the idea in your own words",
                "Read the title only",
                "Skip all questions",
                "Avoid examples",
            ],
            "answer": 0,
            "explanation": "Explaining a concept in your own words is a simple way to check understanding.",
        },
        {
            "question": f"What is a good study habit for {topic}?",
            "options": [
                "Short, consistent study sessions",
                "Only studying before an exam",
                "Never revising",
                "Ignoring difficult areas",
            ],
            "answer": 0,
            "explanation": "Consistent study and revision help reinforce learning.",
        },
    ]
    return [templates[i % len(templates)] for i in range(count)]


def fallback_summary(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(text))
    sentences = [s for s in sentences if s]
    selected = sentences[: min(6, len(sentences))]

    if not selected:
        return "Please enter some educational text to summarize."

    bullets = "\n".join(f"• {sentence}" for sentence in selected)
    return f"{bullets}\n\nTakeaway: Review these key ideas and then test yourself."


def fallback_learning_path(topic: str, level: str) -> str:
    return f"""Learning Path: {topic}
Level: {level}

Week 1 — Foundations
• Learn important terms and core concepts
• Study simple examples
• Practice for 20–30 minutes each day

Week 2 — Core Skills
• Learn the main techniques
• Solve beginner exercises
• Review mistakes and update your notes

Week 3 — Practical Practice
• Solve real or exam-style problems
• Build a small practice project
• Take a short self-test

Week 4 — Review and Challenge
• Study the difficult concepts
• Solve mixed problems
• Complete a final mini-project

Recommendation:
Study consistently, practice actively, and revisit difficult topics every week."""


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "EduGenie API",
        "gemini_configured": bool(
            os.getenv("GEMINI_API_KEY", "").strip()
            and os.getenv("GEMINI_API_KEY", "").strip() != "your_api_key_here"
        ),
    }


@app.get("/api/ask")
def ask_info() -> dict[str, str]:
    return {"message": "Use POST /api/ask with a question."}


@app.post("/api/ask")
def ask(req: QuestionRequest) -> dict[str, str]:
    question = clean_text(req.question)
    prompt = f"""You are EduGenie, a friendly educational tutor.
Answer the student's question accurately using simple language.
Be concise but explain the key idea. Include a small example when useful.
Do not invent facts.

Student question:
{question}"""

    return {"answer": ai_generate(prompt) or fallback_answer(question)}


@app.post("/api/summarize")
def summarize(req: TextRequest) -> dict[str, str]:
    text = clean_text(req.text)
    prompt = f"""Summarize this educational text for a student.
Use 5-8 clear bullet points followed by one short takeaway.
Preserve important facts and do not add unsupported information.

TEXT:
{text}"""

    return {"summary": ai_generate(prompt) or fallback_summary(text)}


@app.post("/api/quiz")
def quiz(req: QuizRequest) -> dict[str, list[dict[str, Any]]]:
    topic = clean_text(req.topic)
    count = req.count

    prompt = f"""Create exactly {count} multiple-choice questions about "{topic}".
Return ONLY valid JSON, with no markdown and no extra text.
Use exactly this format:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": 0,
    "explanation": "Short explanation"
  }}
]
The answer is the zero-based index of the correct option.
Questions must be educational and suitable for students."""

    result = ai_generate(prompt)
    if result:
        parsed = extract_json_array(result)
        if parsed:
            valid = validate_quiz_questions(parsed, count)
            if len(valid) == count:
                return {"questions": valid}

    return {"questions": fallback_quiz(topic, count)}


@app.post("/api/learning-path")
def learning_path(req: PathRequest) -> dict[str, str]:
    topic = clean_text(req.topic)
    level = req.level

    prompt = f"""Create a structured learning path for "{topic}" at {level} level.
Use simple language.
Include stages, weekly topics, practice tasks, a small project idea, and review advice.
Do not claim that external resources were checked."""

    return {"path": ai_generate(prompt) or fallback_learning_path(topic, level)}
