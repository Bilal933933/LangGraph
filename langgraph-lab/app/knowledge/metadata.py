"""اشتقاق ميتاداتا المقطع من المسار النسبي (وظيفة واحدة)."""

Metadata = dict[str, str | None]


def derive_metadata(relpath: str, heading: str) -> Metadata:
    """مسار نسبي + عنوان ← {stage, grade, subject, book_id, lesson} والمجهول None."""
    parts = relpath.replace("\\", "/").strip().strip("/").split("/")
    root = parts[0] if parts else ""
    stage: str | None = None
    grade: str | None = None
    subject: str | None = None
    if root == "textbook" and len(parts) >= 4:
        stage, grade, subject = parts[1], parts[2], parts[3]
    elif root == "references" and len(parts) >= 3:
        stage, subject = parts[1], parts[2]
    lesson = heading.strip().lstrip("#").strip() or None
    return {
        "stage": stage,
        "grade": grade,
        "subject": subject,
        "book_id": subject,
        "lesson": lesson,
    }
