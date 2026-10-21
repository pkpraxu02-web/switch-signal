from __future__ import annotations

import json
import os
import pathlib
import sqlite3
from datetime import datetime, timezone

from .models import Analysis, Review

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, source TEXT, competitor TEXT, rating REAL, title TEXT,
  text TEXT, dislikes TEXT, author TEXT, role TEXT, company_size TEXT, industry TEXT, country TEXT, date TEXT,
  url TEXT, synthetic INTEGER, first_seen TEXT);
CREATE TABLE IF NOT EXISTS analysis(review_id TEXT PRIMARY KEY, persona TEXT, organizer_score INTEGER,
  categories TEXT, primary_cat TEXT, severity REAL, quote TEXT, switch_intent INTEGER, method TEXT, analyzed_at TEXT);
CREATE TABLE IF NOT EXISTS leads(review_id TEXT PRIMARY KEY, score REAL, tier TEXT, rationale TEXT, segment TEXT,
  market TEXT, subject TEXT, body TEXT, draft_check TEXT, status TEXT DEFAULT 'new', updated_at TEXT);
"""


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class Store:
    def __init__(self, path: str | None = None):
        path = path or os.getenv("SWITCHSIGNAL_DB", "data/switchsignal.db")
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def add_reviews(self, reviews: list[Review]) -> int:
        new = 0
        for r in reviews:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO reviews VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r.id, r.source, r.competitor, r.rating, r.title, r.text, r.dislikes, r.author, r.role,
                 r.company_size, r.industry, r.country, r.date, r.url, int(r.synthetic), now()))
            new += cur.rowcount
        self.db.commit()
        return new

    def pending_analysis(self) -> list[Review]:
        rows = self.db.execute("SELECT * FROM reviews WHERE id NOT IN (SELECT review_id FROM analysis)").fetchall()
        return [self._review(r) for r in rows]

    def save_analysis(self, rid: str, a: Analysis) -> None:
        self.db.execute("INSERT OR REPLACE INTO analysis VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (rid, a.persona, a.organizer_score, json.dumps(a.categories), a.primary, a.severity,
                         a.quote, int(a.switch_intent), a.method, now()))
        self.db.commit()

    def analyzed_without_lead(self) -> list[tuple[Review, Analysis]]:
        rows = self.db.execute("SELECT r.id FROM reviews r JOIN analysis a ON a.review_id=r.id "
                               "WHERE r.id NOT IN (SELECT review_id FROM leads)").fetchall()
        return [self.get(r["id"]) for r in rows]

    def get(self, rid: str) -> tuple[Review, Analysis]:
        r = self.db.execute("SELECT * FROM reviews WHERE id=?", (rid,)).fetchone()
        a = self.db.execute("SELECT * FROM analysis WHERE review_id=?", (rid,)).fetchone()
        return self._review(r), Analysis(a["persona"], a["organizer_score"], json.loads(a["categories"]),
                                         a["primary_cat"], a["severity"], a["quote"], bool(a["switch_intent"]),
                                         a["method"])

    def save_lead(self, rid: str, sc: dict, d: dict | None) -> None:
        self.db.execute(
            "INSERT INTO leads(review_id,score,tier,rationale,segment,market,subject,body,draft_check,status,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,'new',?) ON CONFLICT(review_id) DO UPDATE SET score=excluded.score,"
            " tier=excluded.tier, rationale=excluded.rationale, segment=excluded.segment, market=excluded.market,"
            " subject=excluded.subject, body=excluded.body, draft_check=excluded.draft_check, updated_at=excluded.updated_at",
            (rid, sc["score"], sc["tier"], sc["rationale"], sc["segment"], sc["market"],
             d["subject"] if d else "", d["body"] if d else "", d["check"] if d else "no draft (tier C / attendee)", now()))
        self.db.commit()

    def set_status(self, rid: str, status: str) -> bool:
        cur = self.db.execute("UPDATE leads SET status=?, updated_at=? WHERE review_id=?", (status, now(), rid))
        self.db.commit()
        return cur.rowcount > 0

    def leads(self, tier: str = "", category: str = "", competitor: str = "", limit: int = 20) -> list[dict]:
        q = ("SELECT l.*, r.competitor, r.source, r.author, r.role, r.company_size, r.industry, r.country, r.date,"
             " r.rating, r.url, r.synthetic, a.persona, a.primary_cat, a.categories, a.quote, a.switch_intent, a.method"
             " FROM leads l JOIN reviews r ON r.id=l.review_id JOIN analysis a ON a.review_id=l.review_id WHERE 1=1")
        args: list = []
        if tier:
            q += " AND l.tier=?"; args.append(tier)
        if category:
            q += " AND a.primary_cat=?"; args.append(category)
        if competitor:
            q += " AND lower(r.competitor)=lower(?)"; args.append(competitor)
        q += " ORDER BY l.score DESC LIMIT ?"; args.append(limit)
        return [dict(r) for r in self.db.execute(q, args).fetchall()]

    def trends(self, days: int = 90) -> list[dict]:
        q = ("SELECT r.competitor, a.primary_cat AS category, COUNT(*) AS n, ROUND(AVG(a.severity),2) AS avg_severity,"
             " SUM(a.switch_intent) AS switch_signals FROM reviews r JOIN analysis a ON a.review_id=r.id"
             " WHERE a.primary_cat!='' AND a.persona!='attendee' AND r.date >= date('now', ?)"
             " GROUP BY r.competitor, a.primary_cat ORDER BY n DESC")
        return [dict(r) for r in self.db.execute(q, (f"-{days} days",)).fetchall()]

    @staticmethod
    def _review(r: sqlite3.Row) -> Review:
        d = dict(r)
        d.pop("first_seen", None)
        d["synthetic"] = bool(d["synthetic"])
        return Review(**d)
