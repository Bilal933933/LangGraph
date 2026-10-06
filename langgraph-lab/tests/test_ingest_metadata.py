"""عقد اشتقاق الميتاداتا: مسار نسبي ← حقول، والمجهول ← None."""

from app.knowledge.metadata import derive_metadata


def test_textbook_path() -> None:
    meta = derive_metadata("textbook/primary/primary_4/رياضيات/part-01.md", "# الكسور")
    assert meta["stage"] == "primary"
    assert meta["grade"] == "primary_4"
    assert meta["subject"] == "رياضيات"
    assert meta["lesson"] == "الكسور"
    assert meta["book_id"] == "رياضيات"


def test_references_path_without_grade() -> None:
    meta = derive_metadata("references/general/english-foundation-preparatory/part-01.md", "")
    assert meta["grade"] is None
    assert meta["subject"] == "english-foundation-preparatory"
    assert meta["lesson"] is None


def test_unknown_root_gives_nones() -> None:
    meta = derive_metadata("misc/x.md", "# ت")
    assert meta["stage"] is None and meta["grade"] is None
    assert meta["lesson"] == "ت"
