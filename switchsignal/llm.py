"""Optional LLM extraction via ANY OpenAI-compatible endpoint (Ollama, llama.cpp, vLLM, hosted).

Free path: `ollama serve` + `ollama pull llama3.2` then
  LLM_BASE_URL=http://localhost:11434/v1  LLM_MODEL=llama3.2
Off by default. The rules engine always runs; the LLM can only ADD categories and a quote, and only
if its quote is a verbatim substring of the review (hallucination guard in analyze.py).
"""
from __future__ import annotations

import json
import os
import re

import requests

PROMPT = """You label complaints in a software review of an event-ticketing platform.
Return ONLY JSON: {{"categories": [..], "quote": "..."}}.
categories must come from: {cats}. quote must be copied EXACTLY, character for character, from the review
(one sentence or less). If nothing is a complaint, return {{"categories": [], "quote": ""}}.
Review:
\"\"\"{text}\"\"\""""


def configured() -> bool:
    return bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_MODEL"))


def extract(text: str, category_ids: list[str], timeout: int = 30) -> dict | None:
    if not configured():
        return None
    body = {
        "model": os.environ["LLM_MODEL"],
        "temperature": 0,
        "messages": [{"role": "user", "content": PROMPT.format(cats=", ".join(category_ids), text=text[:3000])}],
    }
    headers = {"Authorization": f"Bearer {os.getenv('LLM_API_KEY', 'none')}"}
    try:
        r = requests.post(os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                          json=body, headers=headers, timeout=timeout)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", content, re.S)
        return json.loads(m.group(0)) if m else None
    except Exception:  # network, auth, bad JSON: caller falls back to rules
        return None
