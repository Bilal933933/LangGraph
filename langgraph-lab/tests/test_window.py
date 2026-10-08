"""اختبارات نافذة السياق: بدء آمن بـ human وعدم تيتم ToolMessage."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.graph.window import CONTEXT_WINDOW_MESSAGES, select_window


def test_empty_returns_empty() -> None:
    assert select_window([], 20) == []


def test_zero_limit_returns_empty() -> None:
    msgs = [HumanMessage(content="hi")]
    assert select_window(msgs, 0) == []


def test_short_history_returns_all_starting_human() -> None:
    msgs = [HumanMessage(content="h1"), AIMessage(content="a1")]
    assert [m.type for m in select_window(msgs, 20)] == ["human", "ai"]


def test_drops_leading_ai_until_human() -> None:
    msgs = [
        AIMessage(content="old"),
        HumanMessage(content="h1"),
        AIMessage(content="a1"),
        HumanMessage(content="h2"),
    ]
    window = select_window(msgs, 2)
    assert window and window[0].type == "human"


def test_tool_pair_stays_together() -> None:
    call = {"name": "t", "args": {}, "id": "1", "type": "tool_call"}
    msgs = [
        HumanMessage(content="h1"),
        AIMessage(content="a1"),
        HumanMessage(content="h2"),
        AIMessage(content="a2", tool_calls=[call]),
        ToolMessage(content="r", tool_call_id="1"),
    ]
    assert [m.type for m in select_window(msgs, 3)] == ["human", "ai", "tool"]


def test_all_ai_returns_empty_never_starts_ai() -> None:
    msgs = [AIMessage(content="a"), ToolMessage(content="r", tool_call_id="1")]
    window = select_window(msgs, 2)
    assert window == [] or window[0].type == "human"


def test_default_limit_constant() -> None:
    assert CONTEXT_WINDOW_MESSAGES == 20


def _long_history(total: int) -> list:
    """سجل طويل بالتناوب بشر/آلي، والأحدث بشر دائمًا."""
    msgs = []
    for pos in range(total - 1):
        cls = HumanMessage if pos % 2 == 0 else AIMessage
        msgs.append(cls(content=f"m{pos}"))
    msgs.append(HumanMessage(content="latest"))
    return msgs


def test_newest_message_always_kept() -> None:
    msgs = _long_history(29)
    window = select_window(msgs, 20)
    assert window
    assert window[-1] is msgs[-1]
    assert window[0].type == "human"


def test_newest_kept_when_start_is_not_human() -> None:
    msgs = _long_history(28)
    msgs.insert(8, AIMessage(content="stray"))
    window = select_window(msgs, 20)
    assert window
    assert window[-1] is msgs[-1]
    assert window[0].type == "human"


def test_walk_back_capped_at_double_limit() -> None:
    msgs = [HumanMessage(content="old")]
    msgs += [ToolMessage(content=f"r{i}", tool_call_id=str(i)) for i in range(40)]
    msgs.append(HumanMessage(content="latest"))
    window = select_window(msgs, 10)
    assert len(window) <= 20
    if window:
        assert window[0].type == "human"
        assert window[-1] is msgs[-1]
