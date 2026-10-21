from __future__ import annotations

import hashlib
import pathlib
from dataclasses import dataclass, field

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_yaml(name: str) -> dict:
    return yaml.safe_load((ROOT / "config" / name).read_text(encoding="utf-8"))


@dataclass
class Review:
    source: str
    competitor: str
    text: str
    rating: float | None = None
    title: str = ""
    dislikes: str = ""
    author: str = ""
    role: str = ""
    company_size: str = ""
    industry: str = ""
    country: str = ""
    date: str = ""
    url: str = ""
    synthetic: bool = False
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            key = "|".join([self.source, self.competitor, self.url, self.author,
                            (self.dislikes or self.text)[:120]])
            self.id = hashlib.sha1(key.encode()).hexdigest()[:12]

    def complaint_text(self) -> str:
        """G2/Capterra give a separate 'dislikes' field; classify on that when present."""
        if self.dislikes.strip() and self.dislikes.strip().lower() not in {"nothing", "n/a", "none"}:
            return self.dislikes
        return " ".join(x for x in (self.title, self.text) if x)

    def all_text(self) -> str:
        return " ".join(x for x in (self.title, self.text, self.dislikes) if x)


@dataclass
class Analysis:
    persona: str
    organizer_score: int
    categories: list = field(default_factory=list)  # [{"cat","hits","strong"}]
    primary: str = ""
    severity: float = 0.0
    quote: str = ""
    switch_intent: bool = False
    method: str = "rules"
