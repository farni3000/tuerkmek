"""Konfiguration: .env, Zeitzone, Slots, Pfade."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CARDS_DIR = ROOT / "assets" / "cards"
BITS_DIR = ROOT / "assets" / "bits"
DEFAULT_SLOTS = "08:30,13:00,20:00"


def load_dotenv(path=None):
    """Minimaler .env-Leser – kein python-dotenv nötig.

    Bereits gesetzte Umgebungsvariablen gewinnen, damit man beim Testen
    nicht die Datei anfassen muss.
    """
    path = Path(path) if path else ROOT / ".env"
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_slots(raw):
    slots = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        hours, minutes = part.split(":")
        slots.append(time(int(hours), int(minutes)))
    return sorted(slots)


def parse_ids(raw):
    return {int(part) for part in (raw or "").replace(";", ",").split(",")
            if part.strip().lstrip("-").isdigit()}


@dataclass
class Config:
    token: str
    tz: str
    slots: list
    weekend_off: bool
    slot_window: int
    db_path: Path
    cards_dir: Path
    bits_dir: Path
    log_path: Path
    seed_ids: set

    @property
    def slot_labels(self):
        return [s.strftime("%H:%M") for s in self.slots]


def load_config():
    load_dotenv()

    slots = parse_slots(os.environ.get("TURKMEK_SLOTS", DEFAULT_SLOTS))
    if not slots:
        slots = parse_slots(DEFAULT_SLOTS)

    tz = os.environ.get("TURKMEK_TZ", "Europe/Berlin").strip() or "Europe/Berlin"

    return Config(
        token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        tz=tz,
        slots=slots,
        weekend_off=os.environ.get("TURKMEK_WEEKEND_OFF", "").lower()
        in {"1", "true", "yes"},
        slot_window=int(os.environ.get("TURKMEK_SLOT_WINDOW", "15")),
        db_path=DATA_DIR / "turkmek.db",
        cards_dir=CARDS_DIR,
        bits_dir=BITS_DIR,
        log_path=DATA_DIR / "turkmek.log",
        seed_ids=parse_ids(os.environ.get("TELEGRAM_ALLOWED_IDS", "")),
    )
