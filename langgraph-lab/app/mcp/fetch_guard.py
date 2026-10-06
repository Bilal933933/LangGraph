"""جلب آمن: تحقق SSRF قبل أي شبكة (وظيفة واحدة)."""

import ipaddress
import logging
import socket
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

#: أقصى طول رابط مقبول.
MAX_URL_CHARS = 2000
#: أقصى قفزات تحويل متتابعة (كل قفزة تُتحقق من جديد).
MAX_REDIRECTS = 3
#: مهلة الشبكة الواحدة (ثانية).
FETCH_TIMEOUT = 10.0
#: سقف جسم الصفحة (1MB — ضد الإغراق).
MAX_BODY_BYTES = 1_000_000


class BlockedUrl(ValueError):
    """رابط مرفوض قبل الشبكة."""


def _ip_is_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """IP ← True فقط إن لم يكن خاصًا/حلقيًا/محجوزًا بأي شكل."""
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def host_is_public(host: str) -> bool:
    """مضيف ← True فقط إن حلّت كل عناوينه لعامة (يكشف الترميز العشري)."""
    cleaned = host.strip().strip("[]")
    try:
        return _ip_is_public(ipaddress.ip_address(cleaned))
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(cleaned, None)
    except OSError:
        return False
    addrs = {info[4][0] for info in infos}
    if not addrs:
        return False
    for addr in addrs:
        try:
            if not _ip_is_public(ipaddress.ip_address(str(addr).split("%")[0])):
                return False
        except ValueError:
            return False
    return True


def validate_url(url: str) -> str:
    """رابط ← منظف صالح، أو BlockedUrl قبل أي شبكة."""
    cleaned = (url or "").strip()[:MAX_URL_CHARS]
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise BlockedUrl("الرابط يجب أن يبدأ بـ http:// أو https://.")
    if parsed.username or parsed.password or "@" in parsed.netloc:
        raise BlockedUrl("بيانات اعتماد في الرابط مرفوضة.")
    if not host_is_public(parsed.hostname):
        raise BlockedUrl("المضيف داخلي أو محجوب.")
    return cleaned


def fetch_text(url: str, max_chars: int = 6000) -> str:
    """رابط مُتحقق ← نص مُقتطع، أو رسالة عربية عند أي فشل (لا استثناء)."""
    try:
        current = validate_url(url)
    except BlockedUrl as exc:
        return str(exc)
    try:
        for _ in range(MAX_REDIRECTS + 1):
            with httpx.stream(
                "GET", current, timeout=FETCH_TIMEOUT, follow_redirects=False
            ) as res:
                if res.is_redirect:
                    current = validate_url(urljoin(current, res.headers.get("location", "")))
                    continue
                if res.status_code != 200:
                    return f"تعذر الجلب (HTTP {res.status_code})."
                body = bytearray()
                for chunk in res.iter_bytes(65536):
                    body.extend(chunk)
                    if len(body) > MAX_BODY_BYTES:
                        break
                text = bytes(body).decode(
                    res.charset_encoding or "utf-8", errors="replace"
                ).strip()
            if not text:
                return "الصفحة فارغة."
            safe = max(500, min(int(max_chars), 20000))
            return text[:safe]
        return "تجاوز حد التحويلات."
    except BlockedUrl as exc:
        logger.warning("fetch_blocked url=%r reason=%r", current[:200], str(exc))
        return str(exc)
    except Exception as exc:
        logger.warning("fetch_failed url=%r error=%r", current[:200], exc)
        return "تعذر الجلب الآن."
