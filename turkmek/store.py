"""SQLite-Zustand: was fällig ist, was schon raus ist, was geantwortet wurde.

Ein Nutzer, eine Datei. Zeitstempel liegen als lokale ISO-Minuten
(`YYYY-MM-DDTHH:MM`) in der Datenbank – lesbar beim Debuggen und für den
Vergleich ausreichend.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from . import srs

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id       TEXT PRIMARY KEY,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    item_id      TEXT PRIMARY KEY REFERENCES items(id),
    due_at       TEXT NOT NULL,
    interval_days REAL NOT NULL DEFAULT 0,
    ease         REAL NOT NULL DEFAULT 2.5,
    lapses       INTEGER NOT NULL DEFAULT 0,
    reps         INTEGER NOT NULL DEFAULT 0,
    last_result  TEXT,
    last_seen_at TEXT
);

CREATE TABLE IF NOT EXISTS deliveries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id    TEXT NOT NULL,
    slot       TEXT NOT NULL,
    local_date TEXT NOT NULL,
    sent_at    TEXT NOT NULL,
    message_id INTEGER,
    kind       TEXT NOT NULL DEFAULT 'review',
    status     TEXT NOT NULL DEFAULT 'pending',
    attempts   INTEGER NOT NULL DEFAULT 0,
    UNIQUE(slot, local_date)
);

CREATE TABLE IF NOT EXISTS answers (
    delivery_id INTEGER PRIMARY KEY REFERENCES deliveries(id),
    result      TEXT NOT NULL,
    answered_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def ts(moment):
    return moment.isoformat(timespec="minutes")


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ------------------------------------------------------------ Inhalte --

    def sync_items(self, ids, now):
        """Legt fehlende Wörter an. Vorhandene bleiben unangetastet."""
        added = 0
        for item_id in ids:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO items(id, added_at) VALUES(?, ?)",
                (item_id, ts(now)),
            )
            if cur.rowcount:
                self.conn.execute(
                    "INSERT OR IGNORE INTO reviews(item_id, due_at) VALUES(?, ?)",
                    (item_id, ts(now)),
                )
                added += 1
        self.conn.commit()
        return added

    # ------------------------------------------------------------ Auswahl --

    def due_items(self, now, limit=50):
        return self.conn.execute(
            "SELECT item_id, due_at FROM reviews "
            "WHERE last_seen_at IS NOT NULL AND due_at <= ? "
            "ORDER BY due_at LIMIT ?",
            (ts(now), limit),
        ).fetchall()

    def new_items(self, now, limit=50):
        return self.conn.execute(
            "SELECT item_id, due_at FROM reviews "
            "WHERE last_seen_at IS NULL AND due_at <= ? "
            "ORDER BY due_at LIMIT ?",
            (ts(now), limit),
        ).fetchall()

    def fallback_items(self, limit=50):
        """Zuletzt gesehene zuerst – damit kein Slot leer bleibt."""
        return self.conn.execute(
            "SELECT item_id FROM reviews "
            "ORDER BY COALESCE(last_seen_at, '') ASC LIMIT ?",
            (limit,),
        ).fetchall()

    def seen_today(self, day):
        rows = self.conn.execute(
            "SELECT item_id FROM deliveries WHERE local_date = ?",
            (day.isoformat(),),
        ).fetchall()
        return {r["item_id"] for r in rows}

    def new_today(self, day):
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM deliveries "
            "WHERE local_date = ? AND kind = 'new'",
            (day.isoformat(),),
        ).fetchone()
        return row["n"]

    def review_of(self, item_id):
        return self.conn.execute(
            "SELECT * FROM reviews WHERE item_id = ?", (item_id,)
        ).fetchone()

    # ----------------------------------------------------------- Versand ---

    def delivery(self, slot, day):
        return self.conn.execute(
            "SELECT * FROM deliveries WHERE slot = ? AND local_date = ?",
            (slot, day.isoformat()),
        ).fetchone()

    def delivery_by_id(self, delivery_id):
        return self.conn.execute(
            "SELECT * FROM deliveries WHERE id = ?", (delivery_id,)
        ).fetchone()

    def claim(self, item_id, slot, day, kind, now):
        """Reserviert den Slot. Gibt (id, neu) zurück – nie zwei Karten."""
        try:
            cur = self.conn.execute(
                "INSERT INTO deliveries(item_id, slot, local_date, sent_at, kind) "
                "VALUES(?, ?, ?, ?, ?)",
                (item_id, slot, day.isoformat(), ts(now), kind),
            )
            self.conn.commit()
            return cur.lastrowid, True
        except sqlite3.IntegrityError:
            row = self.delivery(slot, day)
            return (row["id"], False) if row else (None, False)

    def mark_sent(self, delivery_id, message_id, now):
        self.conn.execute(
            "UPDATE deliveries SET status = 'sent', message_id = ?, "
            "attempts = attempts + 1 WHERE id = ?",
            (message_id, delivery_id),
        )

        row = self.delivery_by_id(delivery_id)
        review = self.review_of(row["item_id"]) if row else None
        if review and review["last_seen_at"] is None:
            # Erste Begegnung: morgen wieder.
            due = ts(now + timedelta(days=1))
            self.conn.execute(
                "UPDATE reviews SET last_seen_at = ?, due_at = ? WHERE item_id = ?",
                (ts(now), due, row["item_id"]),
            )
        elif row:
            self.conn.execute(
                "UPDATE reviews SET last_seen_at = ? WHERE item_id = ?",
                (ts(now), row["item_id"]),
            )
        self.conn.commit()

    def mark_failed(self, delivery_id):
        self.conn.execute(
            "UPDATE deliveries SET status = 'failed', attempts = attempts + 1 "
            "WHERE id = ?",
            (delivery_id,),
        )
        self.conn.commit()

    # --------------------------------------------------------- Antworten ---

    def answer(self, delivery_id, result, now):
        """Verarbeitet einen Tap. Gibt (item_id, status) zurück."""
        delivery = self.delivery_by_id(delivery_id)
        if delivery is None:
            return None, "unknown"

        done = self.conn.execute(
            "SELECT 1 FROM answers WHERE delivery_id = ?", (delivery_id,)
        ).fetchone()
        if done:
            return delivery["item_id"], "duplicate"

        review = self.review_of(delivery["item_id"])
        if review is None:
            return delivery["item_id"], "unknown"

        state = srs.apply(
            result,
            review["reps"],
            review["interval_days"],
            review["ease"],
            review["lapses"],
        )

        self.conn.execute(
            "UPDATE reviews SET reps = ?, interval_days = ?, ease = ?, "
            "lapses = ?, last_result = ?, due_at = ? WHERE item_id = ?",
            (
                state["reps"],
                state["interval"],
                state["ease"],
                state["lapses"],
                result,
                ts(now + timedelta(days=state["interval"])),
                delivery["item_id"],
            ),
        )
        self.conn.execute(
            "INSERT INTO answers(delivery_id, result, answered_at) VALUES(?, ?, ?)",
            (delivery_id, result, ts(now)),
        )
        self.conn.commit()
        return delivery["item_id"], "ok"

    # ------------------------------------------------------------ Statistik --

    def stats(self, today):
        total = self.conn.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        due = self.conn.execute(
            "SELECT COUNT(*) AS n FROM reviews WHERE due_at <= ?",
            (ts(today),),
        ).fetchone()["n"]
        answered = self.conn.execute(
            "SELECT COUNT(*) AS n FROM answers"
        ).fetchone()["n"]
        good = self.conn.execute(
            "SELECT COUNT(*) AS n FROM answers WHERE result = 'y'"
        ).fetchone()["n"]

        return {
            "total": total,
            "due": due,
            "answered": answered,
            "good": good,
            "accuracy": (good / answered) if answered else 0.0,
            "streak": self.streak(today),
        }

    def streak(self, today):
        rows = self.conn.execute(
            "SELECT DISTINCT d.local_date AS day FROM answers a "
            "JOIN deliveries d ON d.id = a.delivery_id"
        ).fetchall()
        days = {r["day"] for r in rows}

        cursor = today.date()
        if cursor.isoformat() not in days:
            cursor -= timedelta(days=1)

        count = 0
        while cursor.isoformat() in days:
            count += 1
            cursor -= timedelta(days=1)
        return count

    # ------------------------------------------------------------ Settings --

    def get_setting(self, key, default=None):
        row = self.conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key, value):
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.conn.commit()

    def allowed_ids(self):
        raw = self.get_setting("allowed_ids", "")
        return {int(x) for x in raw.split(",") if x.strip().lstrip("-").isdigit()}

    def add_allowed(self, user_id):
        ids = self.allowed_ids()
        ids.add(int(user_id))
        self.set_setting("allowed_ids", ",".join(str(i) for i in sorted(ids)))

    def reset(self, item_id):
        self.conn.execute(
            "UPDATE reviews SET due_at = ?, interval_days = 0, ease = 2.5, "
            "lapses = 0, reps = 0, last_result = NULL, last_seen_at = NULL "
            "WHERE item_id = ?",
            (ts(datetime.now()), item_id),
        )
        self.conn.commit()
