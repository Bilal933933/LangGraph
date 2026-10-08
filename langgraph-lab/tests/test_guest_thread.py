"""اختبارات خيط الضيف: عزل best-effort ببصمة بلا تصادم قص."""

from app.services.chat_service import ChatService


def test_same_ip_different_raw_differ() -> None:
    a = ChatService.guest_thread_id("1.2.3.4", "a" * 60)
    b = ChatService.guest_thread_id("1.2.3.4", "b" * 60)
    assert a != b


def test_different_ip_same_raw_differ() -> None:
    a = ChatService.guest_thread_id("1.2.3.4", "default")
    b = ChatService.guest_thread_id("5.6.7.8", "default")
    assert a != b


def test_deterministic_and_bounded() -> None:
    a = ChatService.guest_thread_id("1.2.3.4", "default")
    assert ChatService.guest_thread_id("1.2.3.4", "default") == a
    assert len(a) <= 64
    assert ChatService.parse_thread_id(a) == (None, None)


def test_empty_inputs_fall_back() -> None:
    out = ChatService.guest_thread_id("", "")
    assert out.startswith("g:") and len(out) <= 64
