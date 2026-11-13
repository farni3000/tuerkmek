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

# Eine Karte, die länger als das hier unbeantwortet herumliegt, ist keine
# Wiederholung mehr, sondern ein alter Knopf. Solche Taps werden verworfen,
# damit sie den aktuellen Plan nicht rückwirkend verschieben.
MAX_ANSWER_AGE = timedelta(hours=24)

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

CREATE TABLE IF NOT EXISTS bit_reviews (
    bit_id       TEXT PRIMARY KEY,
    due_at       TEXT NOT NULL,
    interval_days REAL NOT NULL DEFAULT 0,
    ease         REAL NOT NULL DEFAULT 2.5,
    lapses       INTEGER NOT NULL DEFAULT 0,
    reps         INTEGER NOT NULL DEFAULT 0,
    last_result  TEXT,
    last_seen_at TEXT,
    retired_at   TEXT
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
        # Der Bot und ein manueller Aufruf können gleichzeitig schreiben.
        # WAL kann fehlschlagen, wenn ein alter Prozess die Datei noch hält –
        # dann bleibt es beim Standardmodus, was auch funktioniert.
        self.conn.execute("PRAGMA busy_timeout=5000")
        try:
            self.conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
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

    def sync_bits(self, ids, now):
        """Legt fehlende Grammatik-Bits an. Alter Zustand bleibt stehen."""
        added = 0
        for bit_id in ids:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO bit_reviews(bit_id, due_at) VALUES(?, ?)",
                (bit_id, ts(now)),
            )
            added += cur.rowcount
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

    def due_bits(self, now, limit=50):
        return self.conn.execute(
            "SELECT bit_id, due_at FROM bit_reviews "
            "WHERE retired_at IS NULL AND last_seen_at IS NOT NULL "
            "AND due_at <= ? ORDER BY due_at LIMIT ?",
            (ts(now), limit),
        ).fetchall()

    def new_bits(self, now, limit=50):
        return self.conn.execute(
            "SELECT bit_id, due_at FROM bit_reviews "
            "WHERE retired_at IS NULL AND last_seen_at IS NULL "
            "AND due_at <= ? ORDER BY due_at LIMIT ?",
            (ts(now), limit),
        ).fetchall()

    def fallback_bits(self, limit=50):
        """Alle aktiven Bits, die am längsten nicht dran waren."""
        return self.conn.execute(
            "SELECT bit_id FROM bit_reviews "
            "WHERE retired_at IS NULL "
            "ORDER BY COALESCE(last_seen_at, '') ASC, bit_id LIMIT ?",
            (limit,),
        ).fetchall()

    def seen_today(self, day):
        rows = self.conn.execute(
            "SELECT item_id FROM deliveries "
            "WHERE local_date = ? AND kind != 'bit'",
            (day.isoformat(),),
        ).fetchall()
        return {r["item_id"] for r in rows}

    def bits_today(self, day):
        """Alle Bits, die heute schon gezeigt oder reserviert wurden."""
        rows = self.conn.execute(
            "SELECT item_id FROM deliveries "
            "WHERE local_date = ? AND kind = 'bit'",
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

    def bit_review_of(self, bit_id):
        return self.conn.execute(
            "SELECT * FROM bit_reviews WHERE bit_id = ?", (bit_id,)
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
        if row and row["kind"] == "bit":
            review = self.bit_review_of(row["item_id"])
            if review and review["last_seen_at"] is None:
                due = ts(now + timedelta(days=1))
                self.conn.execute(
                    "UPDATE bit_reviews SET last_seen_at = ?, due_at = ? "
                    "WHERE bit_id = ?",
                    (ts(now), due, row["item_id"]),
                )
            elif review:
                self.conn.execute(
                    "UPDATE bit_reviews SET last_seen_at = ? WHERE bit_id = ?",
                    (ts(now), row["item_id"]),
                )
            self.conn.commit()
            return

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

    def retire_bit(self, delivery_id, now):
        """Nimmt ein Bit dauerhaft aus der Auswahl.

        Das ist eine Präferenz, keine Quizantwort – deshalb gilt hier bewusst
        keine 24-Stunden-Grenze. Ein alter „nicht mehr zeigen“-Tap soll
        trotzdem wirken.
        """
        delivery = self.delivery_by_id(delivery_id)
        if delivery is None or delivery["kind"] != "bit":
            return None, "unknown"

        review = self.bit_review_of(delivery["item_id"])
        if review is None:
            return delivery["item_id"], "unknown"
        if review["retired_at"]:
            return delivery["item_id"], "duplicate"

        self.conn.execute(
            "UPDATE bit_reviews SET retired_at = ? WHERE bit_id = ?",
            (ts(now), delivery["item_id"]),
        )
        self.conn.commit()
        return delivery["item_id"], "ok"

    # --------------------------------------------------------- Antworten ---

    def answer(self, delivery_id, result, now, max_age=MAX_ANSWER_AGE):
        """Verarbeitet einen Tap. Gibt (item_id, status) zurück.

        Status ist "ok", "duplicate" (schon beantwortet), "stale" (Karte zu
        alt) oder "unknown" (Lieferung fehlt). Die Antwort wird zuerst
        geschrieben; nur wer sie tatsächlich anlegen konnte, darf auch den
        Review-Zustand fortschreiben. Dadurch zählt ein Doppeltap nie doppelt.
        """
        delivery = self.delivery_by_id(delivery_id)
        if delivery is None:
            return None, "unknown"

        review = self.review_of(delivery["item_id"])
        if review is None:
            return delivery["item_id"], "unknown"

        # Nur für die richtige Rückmeldung; verbindlich ist der INSERT unten.
        done = self.conn.execute(
            "SELECT 1 FROM answers WHERE delivery_id = ?", (delivery_id,)
        ).fetchone()
        if done:
            return delivery["item_id"], "duplicate"

        if max_age is not None:
            sent_at = datetime.fromisoformat(delivery["sent_at"])
            if now - sent_at > max_age:
                return delivery["item_id"], "stale"

        with self.conn:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO answers(delivery_id, result, answered_at) "
                "VALUES(?, ?, ?)",
                (delivery_id, result, ts(now)),
            )
            if not cur.rowcount:
                return delivery["item_id"], "duplicate"

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
        return delivery["item_id"], "ok"

    def answer_bit(self, delivery_id, result, now, max_age=MAX_ANSWER_AGE):
        """Verarbeitet eine Quizantwort auf ein Grammatik-Bit.

        Gleiche Strenge wie bei Wörtern: Duplikate und alte Taps ändern den
        Plan nicht. Ein bereits abgeschaltetes Bit bleibt abgeschaltet.
        """
        delivery = self.delivery_by_id(delivery_id)
        if delivery is None or delivery["kind"] != "bit":
            return None, "unknown"

        review = self.bit_review_of(delivery["item_id"])
        if review is None:
            return delivery["item_id"], "unknown"
        if review["retired_at"]:
            return delivery["item_id"], "duplicate"

        done = self.conn.execute(
            "SELECT 1 FROM answers WHERE delivery_id = ?", (delivery_id,)
        ).fetchone()
        if done:
            return delivery["item_id"], "duplicate"

        if max_age is not None:
            sent_at = datetime.fromisoformat(delivery["sent_at"])
            if now - sent_at > max_age:
                return delivery["item_id"], "stale"

        with self.conn:
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO answers(delivery_id, result, answered_at) "
                "VALUES(?, ?, ?)",
                (delivery_id, result, ts(now)),
            )
            if not cur.rowcount:
                return delivery["item_id"], "duplicate"

            state = srs.apply(
                result,
                review["reps"],
                review["interval_days"],
                review["ease"],
                review["lapses"],
            )

            self.conn.execute(
                "UPDATE bit_reviews SET reps = ?, interval_days = ?, ease = ?, "
                "lapses = ?, last_result = ?, due_at = ? WHERE bit_id = ?",
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
        return delivery["item_id"], "ok"

    # ------------------------------------------------------------ Statistik --

    def stats(self, today):
        total = self.conn.execute("SELECT COUNT(*) AS n FROM reviews").fetchone()["n"]
        due = self.conn.execute(
            "SELECT COUNT(*) AS n FROM reviews WHERE due_at <= ?",
            (ts(today),),
        ).fetchone()["n"]
        answered = self.conn.execute(
            "SELECT COUNT(*) AS n FROM answers a "
            "JOIN deliveries d ON d.id = a.delivery_id "
            "WHERE d.kind != 'bit'"
        ).fetchone()["n"]
        good = self.conn.execute(
            "SELECT COUNT(*) AS n FROM answers a "
            "JOIN deliveries d ON d.id = a.delivery_id "
            "WHERE d.kind != 'bit' AND a.result = 'y'"
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
            "JOIN deliveries d ON d.id = a.delivery_id "
            "WHERE d.kind != 'bit'"
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
