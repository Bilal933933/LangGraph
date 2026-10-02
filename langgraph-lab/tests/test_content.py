"""اختبار مرشح النص: كتل التفكير تُتجاهل ويبقى النص فقط."""

from app.graph.content import message_text


def test_plain_string_passes_through() -> None:
    assert message_text("مرحبا") == "مرحبا"


def test_thinking_blocks_are_dropped() -> None:
    content: object = [
        {"thought_signature": "EmAKXgFpFH0TntZV6AlSjmFhy5B9GAXWRmcG0="},
        {"type": "text", "text": "أهلا بك!"},
        "تابع الرد",
    ]
    assert message_text(content) == "أهلا بك! تابع الرد"


def test_empty_blocks_yield_empty_string() -> None:
    content: object = [{"thought_signature": "abc"}, {"type": "image"}]
    assert message_text(content) == ""
