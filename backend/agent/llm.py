"""LLM client with graceful mock fallback.

If GEMINI_API_KEY is set, uses Gemini for extraction and reply drafting.
Otherwise falls back to a deterministic heuristic so the whole app is
runnable and demoable with zero API keys configured.
"""
from __future__ import annotations
import json
import os
import re
from typing import Any

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

_gemini_ready = False
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        _model = genai.GenerativeModel(GEMINI_MODEL)
        _gemini_ready = True
    except Exception:
        _gemini_ready = False


def llm_mode() -> str:
    return "live" if _gemini_ready else "mock"


def _extract_json(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


EXTRACTION_PROMPT = """You are a lead-intake assistant. Read the raw inbound lead text below and
extract structured fields. Respond with ONLY a JSON object, no markdown fences, no commentary.

Fields:
- name: person's name if present, else null
- company: company/organization name if present, else null
- contact: best contact detail found (email or phone), else null
- need: one-sentence summary of what they want built/solved
- urgency: one of "hot", "warm", "cold" based on tone/timeline signals (hot = mentions deadline/ready to start/budget ready, cold = vague/just browsing, warm = otherwise)
- budget_hint: any budget/timeline signal mentioned, else null

Raw lead:
---
{raw_text}
---

JSON:"""

REPLY_PROMPT = """You are drafting a first-reply email on behalf of a freelance full-stack + GenAI developer.
Keep it short (4-6 sentences), warm but professional, reference something specific from their message,
and end with a clear next step (e.g. a quick call). Do not invent details not present in the lead.
Sign off as "Dileep".

Lead (raw): {raw_text}

Extracted summary: {need}

Write only the email body, no subject line, no markdown."""


def extract_lead(raw_text: str) -> dict[str, Any]:
    if _gemini_ready:
        try:
            resp = _model.generate_content(EXTRACTION_PROMPT.format(raw_text=raw_text))
            data = _extract_json(resp.text)
            if data:
                data.setdefault("urgency", "unknown")
                return data
        except Exception:
            pass
    return _mock_extract(raw_text)


def draft_reply(raw_text: str, need: str, urgency: str = "warm") -> str:
    if _gemini_ready:
        try:
            resp = _model.generate_content(REPLY_PROMPT.format(raw_text=raw_text, need=need or "a new project"))
            if resp.text and resp.text.strip():
                return resp.text.strip()
        except Exception:
            pass
    return _mock_reply(raw_text, need, urgency)


# ---- Mock / heuristic fallback (zero API keys needed) ----

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\s\-()]{8,}\d)")
_URGENT_WORDS = ["asap", "urgent", "this week", "deadline", "ready to start", "budget approved", "launch"]
_COLD_WORDS = ["just curious", "just exploring", "no timeline", "someday", "browsing"]


_GREETING_WORDS = {"hey", "hi", "hello", "dear", "greetings", "good", "morning", "afternoon", "evening", "yo", "hiya"}


def _word_safe_truncate(text: str, max_len: int) -> str:
    """Trim to max_len without cutting mid-word, appending an ellipsis if trimmed."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0].rstrip(",;:-") + "…"


def _guess_name(text: str) -> str | None:
    m = re.search(
        r"(?:my name is|this is|i'?m|i am)\s+([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?)",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()

    first_line = text.strip().splitlines()[0] if text.strip() else ""
    m2 = re.match(r"^([A-Z][a-zA-Z'-]+(?:\s+[A-Z][a-zA-Z'-]+)?)[,:-]", first_line)
    if m2 and m2.group(1).strip().lower() not in _GREETING_WORDS:
        return m2.group(1).strip()
    return None


def _guess_company(text: str) -> str | None:
    m = re.search(r"(?:at|from|with)\s+([A-Z][\w&-]+(?:\s+[A-Z][\w&-]+){0,2})", text)
    if m:
        company = m.group(1).strip()
        # don't bleed into the next sentence
        company = re.split(r"\.\s", company)[0].rstrip(".")
        return company
    return None


def _mock_extract(text: str) -> dict[str, Any]:
    email = _EMAIL_RE.search(text)
    phone = _PHONE_RE.search(text)
    lower = text.lower()
    urgency = "warm"
    if any(w in lower for w in _URGENT_WORDS):
        urgency = "hot"
    elif any(w in lower for w in _COLD_WORDS):
        urgency = "cold"

    need_sentence = None
    keywords = ["need", "want", "looking for", "build", "help", "automate", "chatbot", "agent", "wondering if"]
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if any(k in sent.lower() for k in keywords):
            need_sentence = sent.strip()
            break
    if not need_sentence:
        first_line = text.strip().split("\n")[0]
        need_sentence = _word_safe_truncate(first_line, 157)

    budget_hint = None
    m = re.search(r"(\$[\d,]+(?:k|K)?(?:\s*-\s*\$?[\d,]+(?:k|K)?)?|\bbudget\b[^.\n]{0,60})", text)
    if m:
        budget_hint = _word_safe_truncate(m.group(0).strip(), 40)

    return {
        "name": _guess_name(text),
        "company": _guess_company(text),
        "contact": email.group(0) if email else (phone.group(0).strip() if phone else None),
        "need": need_sentence,
        "urgency": urgency,
        "budget_hint": budget_hint,
    }


def _mock_reply(text: str, need: str, urgency: str = "warm") -> str:
    name = _guess_name(text) or "there"
    need_txt = (need or "what you're working on").rstrip(".")

    if urgency == "hot":
        body = (
            f"Thanks for the detail — this sounds like exactly the kind of project I take on, "
            f"and I can move quickly. Based on what you shared — \"{need_txt}\" — I'd love to "
            f"jump on a short call this week to lock down scope and get started."
        )
    elif urgency == "cold":
        body = (
            f"Thanks for reaching out and for the context. Regarding \"{need_txt}\" — happy to "
            f"share more about how I typically work and rough ranges once you have a clearer "
            f"sense of what you're looking for. No pressure at all, just let me know when it's "
            f"useful to talk."
        )
    else:
        body = (
            f"Thanks for reaching out — sounds like a good fit for what I build. Regarding "
            f"\"{need_txt}\" specifically, I'd love to hear a bit more about scope and timeline."
        )

    cta = "Do you have 15 minutes this week for a quick call?" if urgency != "cold" else "Feel free to reply whenever it's useful."

    return f"Hi {name},\n\n{body}\n\n{cta} Happy to work around your schedule.\n\nBest,\nDileep"
