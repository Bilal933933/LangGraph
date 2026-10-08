"""العرض الحتمي للمخرجات (Renderer فقط، بلا LLM)."""

from app.rendering.registry import (
    SUPPORTED_INTENTS,
    output_schema_for,
    render_for_intent,
    render_teacher_copy,
)

__all__ = ["SUPPORTED_INTENTS", "output_schema_for", "render_for_intent", "render_teacher_copy"]

