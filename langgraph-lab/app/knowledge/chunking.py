"""تقطيع ماركداون حتمي: نفس الدخل ← نفس المقاطع دائمًا (وظيفة واحدة)."""

import hashlib
import re
from dataclasses import dataclass

#: عناوين المستويات 1-3 فقط (الأعمق تفصيل زائد عن الاسترجاع).
_HEADING = re.compile(r"(?m)^(#{1,3})\s+(.+?)\s*$")


@dataclass(frozen=True)
class Chunk:
    """مقطع واحد: عنوان قسمه + نصه + ترتيبه + عدد كلماته."""

    title: str
    text: str
    index: int
    token_count: int


def doc_key_for(relpath: str) -> str:
    """مسار نسبي ← بصمة sha256 ثابتة (تطبيع الفواصل أولًا)."""
    normalized = relpath.replace("\\", "/").strip().strip("/")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _windows(words: list[str], max_chars: int, overlap: int) -> list[list[str]]:
    """كلمات ← نوافذ بحد أحرف مع تراكب الذيول (حتمي بلا عشوائية)."""
    out: list[list[str]] = []
    cur: list[str] = []
    cur_len = 0
    for word in words:
        add = len(word) + (1 if cur else 0)
        if cur and cur_len + add > max_chars:
            out.append(cur)
            seed = cur[-overlap:] if overlap > 0 else []
            while seed and sum(len(w) for w in seed) + len(seed) - 1 >= max_chars:
                seed = seed[1:]
            cur = seed
            cur_len = sum(len(w) for w in cur) + max(len(cur) - 1, 0)
            add = len(word) + (1 if cur else 0)
        cur.append(word)
        cur_len += add
    if cur:
        out.append(cur)
    return out


def split_markdown(text: str, max_chars: int = 2000, overlap_words: int = 50) -> list[Chunk]:
    """نص ماركداون ← مقاطع بعناوينها؛ الطويل يُشطر بتراكب كلمات."""
    matches = list(_HEADING.finditer(text or ""))
    sections: list[tuple[str, str]] = []
    if not matches:
        body = (text or "").strip()
        if body:
            sections.append(("", body))
    else:
        head = text[: matches[0].start()].strip()
        if head:
            sections.append(("", head))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[match.end() : end].strip()
            if body:
                sections.append((match.group(2).strip(), body))
    chunks: list[Chunk] = []
    for title, body in sections:
        for window in _windows(body.split(), max_chars, overlap_words):
            piece = " ".join(window)
            chunks.append(
                Chunk(
                    title=title,
                    text=piece,
                    index=len(chunks),
                    token_count=len(window),
                )
            )
    return chunks
