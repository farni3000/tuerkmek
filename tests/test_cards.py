from turkmek import cards

WORD = {
    "id": "kapi",
    "tr": "kapı",
    "de": "die Tür",
    "example": {"tr": "Kapıyı kapatır mısın?", "de": "Machst du die Tür zu?"},
}


def test_caption_has_word_and_example():
    text = cards.caption(WORD)
    assert "kapı" in text
    assert "die Tür" in text
    assert "Kapıyı kapatır mısın?" in text
    assert "Machst du die Tür zu?" in text


def test_caption_with_status():
    text = cards.caption(WORD, status=cards.STATUS["y"])
    assert text.endswith(cards.STATUS["y"])


def test_new_word_has_no_buttons():
    assert cards.keyboard(1, "new") is None


def test_review_keyboard_has_two_buttons():
    markup = cards.keyboard(42, "review")
    buttons = markup["inline_keyboard"][0]
    assert len(buttons) == 2
    assert buttons[0]["callback_data"] == "a:42:y"
    assert buttons[1]["callback_data"] == "a:42:n"


def test_callback_data_stays_small():
    # Telegram erlaubt maximal 64 Bytes pro callback_data.
    for button in cards.keyboard(999999, "review")["inline_keyboard"][0]:
        assert len(button["callback_data"].encode()) <= 64


def test_parse_callback_roundtrip():
    assert cards.parse_callback("a:42:y") == (42, "y")
    assert cards.parse_callback("a:42:n") == (42, "n")


def test_parse_callback_rejects_garbage():
    for data in (None, "", "x:1:y", "a:1", "a:abc:y", "a:1:z"):
        assert cards.parse_callback(data) is None


def test_button_text_is_bilingual():
    markup = cards.keyboard(1, "review")
    good, again = markup["inline_keyboard"][0]
    assert "Biliyorum" in good["text"] and "Gewusst" in good["text"]
    assert "Tekrar" in again["text"] and "Nochmal" in again["text"]
