#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  echo "Usage: $0"
  exit 0
fi

if [ ! -d .venv ]; then
  echo "Erstelle virtuelle Umgebung …"
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  .venv/bin/pip install --quiet -r requirements.txt
fi

if [ ! -f .env ]; then
  echo "Hinweis: .env fehlt – cp .env.example .env und TELEGRAM_BOT_TOKEN eintragen." >&2
fi

exec .venv/bin/python -m turkmek.bot
