"""اختبارات حارس SSRF: عناوين محظورة تُرفض قبل أي شبكة."""

from typing import Any

import pytest

from app.mcp import fetch_guard
from app.mcp.fetch_guard import BlockedUrl, fetch_text, validate_url


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/x",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "http://user:pass@example.com/",
        "http://127.0.0.1/admin",
        "http://10.0.0.5/",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://2130706433/",  # 127.0.0.1 عشريًا
        "",
        "   ",
    ],
)
def test_blocked_urls_raise_before_network(url: str) -> None:
    with pytest.raises(BlockedUrl):
        validate_url(url)


def test_public_url_passes_validation() -> None:
    assert validate_url("https://93.184.216.34/page?a=1") == "https://93.184.216.34/page?a=1"


def test_url_is_trimmed_and_capped() -> None:
    assert validate_url("  https://93.184.216.34/  ") == "https://93.184.216.34/"
    assert len(validate_url("https://93.184.216.34/" + "a" * 3000)) <= 2000


class _FakeStream:
    """بديل httpx.stream: استجابة ثابتة بلا شبكة."""

    def __init__(
        self,
        *,
        is_redirect: bool = False,
        status: int = 200,
        location: str = "",
        body: bytes = b"hello world",
    ) -> None:
        self.is_redirect = is_redirect
        self.status_code = status
        self.headers = {"location": location}
        self.charset_encoding = "utf-8"
        self._body = body

    def __enter__(self) -> "_FakeStream":
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def iter_bytes(self, size: int) -> Any:
        _ = size
        yield self._body


def test_fetch_success_path_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        fetch_guard.httpx, "stream", lambda *a, **k: _FakeStream(body=("أهلاً " * 5000).encode())
    )
    assert fetch_text("https://93.184.216.34/", max_chars=6000) == ("أهلاً " * 5000)[:6000]


def test_redirect_to_private_is_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        fetch_guard.httpx,
        "stream",
        lambda *a, **k: _FakeStream(is_redirect=True, location="http://127.0.0.1/x"),
    )
    assert fetch_text("https://93.184.216.34/") == "المضيف داخلي أو محجوب."
