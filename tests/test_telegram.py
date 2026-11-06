"""Der Client muss die camelCase-Methodennamen der Bot-API treffen.

Telegram beantwortet falsch geschriebene Methoden wie `send_message` mit
404 Not Found. Die übrigen Tests nutzen FakeTelegram und würden das nie
bemerken, deshalb prüft dieser Test die tatsächlich aufgerufenen Pfade.
"""

import asyncio

import httpx

from turkmek.telegram import Telegram


def called_methods(action):
    async def run():
        seen = []

        def handler(request):
            seen.append(request.url.path.rsplit("/", 1)[-1])
            return httpx.Response(
                200, json={"ok": True, "result": {"message_id": 1}}
            )

        telegram = Telegram("123456:test-token")
        await telegram._client.aclose()
        telegram._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        )
        try:
            await action(telegram)
        finally:
            await telegram.close()
        return seen

    return asyncio.run(run())


def test_send_message_uses_camel_case():
    assert called_methods(
        lambda tg: tg.send_message(1, "hallo")
    ) == ["sendMessage"]


def test_send_photo_uses_camel_case(tmp_path):
    card = tmp_path / "kapi.jpg"
    card.write_bytes(b"\xff\xd8\xff")

    assert called_methods(
        lambda tg: tg.send_photo(1, card, "Kapi")
    ) == ["sendPhoto"]


def test_edit_caption_uses_camel_case():
    assert called_methods(
        lambda tg: tg.edit_caption(1, 2, "caption")
    ) == ["editMessageCaption"]


def test_get_updates_uses_camel_case():
    assert called_methods(
        lambda tg: tg.get_updates(0)
    ) == ["getUpdates"]


def test_answer_callback_uses_camel_case():
    assert called_methods(
        lambda tg: tg.answer_callback("cb")
    ) == ["answerCallbackQuery"]
