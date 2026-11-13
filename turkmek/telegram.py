"""Dünner Telegram-Client.

Long Polling statt Webhook: kein offener Port, kein HTTPS-Zertifikat, läuft
auch hinter einem Router. Für einen einzigen Nutzer ist das die einfachere
und robustere Variante.
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
from pathlib import Path

import httpx

log = logging.getLogger(__name__)


class TelegramError(RuntimeError):
    pass


class Telegram:
    def __init__(self, token):
        self._base = f"https://api.telegram.org/bot{token}"
        # Der Long-Poll-Timeout liegt bei 30 s, der HTTP-Timeout darüber.
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(45.0, connect=10.0)
        )

    async def close(self):
        await self._client.aclose()

    async def _call(self, method, data=None, files=None, retries=2):
        last_error = None

        for attempt in range(retries + 1):
            try:
                response = await self._client.post(
                    f"{self._base}/{method}", data=data, files=files
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= retries:
                    raise TelegramError(f"{method}: {exc}") from exc
                await asyncio.sleep(2 * (attempt + 1))
                continue

            try:
                payload = response.json()
            except ValueError:
                raise TelegramError(f"{method}: keine JSON-Antwort "
                                    f"({response.status_code})")

            if payload.get("ok"):
                return payload.get("result")

            if response.status_code == 429:
                wait = payload.get("parameters", {}).get("retry_after", 3)
                log.warning("Rate Limit, warte %ss", wait)
                if attempt >= retries:
                    raise TelegramError(f"{method}: Rate Limit")
                await asyncio.sleep(wait)
                continue

            description = payload.get("description", "unbekannter Fehler")
            raise TelegramError(f"{method}: {description}")

        raise TelegramError(f"{method}: {last_error}")

    # ------------------------------------------------------------- Senden --

    async def send_photo(self, chat_id, path, caption, reply_markup=None):
        path = Path(path)
        data = {"chat_id": str(chat_id), "caption": caption}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

        # Bytes statt Dateihandle, damit ein Retry nicht auf einem
        # geschlossenen Handle landet.
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        files = {"photo": (path.name, path.read_bytes(), mime)}
        return await self._call("sendPhoto", data=data, files=files)

    async def send_message(self, chat_id, text, reply_markup=None):
        data = {"chat_id": str(chat_id), "text": text,
                "disable_web_page_preview": "true"}
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        return await self._call("sendMessage", data=data)

    async def edit_caption(self, chat_id, message_id, caption,
                           reply_markup=None):
        data = {
            "chat_id": str(chat_id),
            "message_id": str(message_id),
            "caption": caption,
            "reply_markup": json.dumps(reply_markup or {"inline_keyboard": []}),
        }
        try:
            return await self._call("editMessageCaption", data=data)
        except TelegramError as exc:
            # "message is not modified" ist harmlos; alles andere heißt, dass
            # die Buttons stehen bleiben und erneut getippt wird.
            if "message is not modified" in str(exc):
                log.debug("Caption-Edit ohne Änderung: %s", exc)
            else:
                log.warning("Caption-Edit fehlgeschlagen: %s", exc)
            return None

    # ------------------------------------------------------------ Empfangen --

    async def get_updates(self, offset, timeout=30):
        data = {"offset": str(offset), "timeout": str(timeout),
                "allowed_updates": json.dumps(["message", "callback_query"])}
        return await self._call("getUpdates", data=data) or []

    async def answer_callback(self, callback_id, text=None):
        data = {"callback_query_id": str(callback_id)}
        if text:
            data["text"] = text
        try:
            return await self._call("answerCallbackQuery", data=data)
        except TelegramError as exc:
            log.warning("Callback-Antwort fehlgeschlagen: %s", exc)
            return None
