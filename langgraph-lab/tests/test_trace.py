"""اختبارات التتبع: مراحل رد النموذج تُسجل في ملف."""

from pathlib import Path

from langchain_core.messages import HumanMessage

from app.core.trace import get_logger, setup_logging, stage
from app.graph.nodes.answer import make_answer_node


class FakeModel:
    """نموذج وهمي للتحقق من تسجيل المراحل بلا Gemini."""

    def invoke(self, messages: list[object]) -> object:
        from langchain_core.messages import AIMessage

        return AIMessage(content=f"fake-reply-to-{len(messages)}-messages")


def test_setup_logging_writes_to_file(tmp_path: Path) -> None:
    """تهيئة اللوجر ← ملف app.log موجود وقابل للكتابة."""
    log_file = setup_logging(log_dir=tmp_path, level="DEBUG")
    assert log_file.name == "app.log"
    get_logger().info("trace-smoke-test")
    assert "trace-smoke-test" in log_file.read_text(encoding="utf-8")


def test_stage_context_logs_start_end_with_latency(tmp_path: Path) -> None:
    """سياق المرحلة ← سطرا بداية ونهاية مع latency_ms."""
    log_file = setup_logging(log_dir=tmp_path, level="DEBUG")
    with stage(get_logger(), "answer.build_prompt", window=3):
        pass
    text = log_file.read_text(encoding="utf-8")
    assert "answer.build_prompt" in text
    assert "latency_ms" in text


def test_answer_node_logs_reply_stages(tmp_path: Path) -> None:
    """عقدة الإجابة ← المراحل الثلاث في الملف (موجه/استدعاء/رد)."""
    log_file = setup_logging(log_dir=tmp_path, level="DEBUG")
    node = make_answer_node(FakeModel())  # type: ignore[arg-type]
    result = node({"messages": [HumanMessage(content="مرحبا")]})
    assert len(result["messages"]) == 1
    text = log_file.read_text(encoding="utf-8")
    assert "answer.build_prompt" in text
    assert "answer.model_invoke" in text
    assert "answer.reply" in text
