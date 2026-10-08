"""اختبارات البث: مراحل ← رموز ← إتمام، بلا شبكة ولا مفاتيح."""

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage

from app.graph.streaming import encode_sse, stream_run


class FakeStreamGraph:
    """رسم وهمي يبث tuples جاهزة بصيغة langgraph (mode, data)."""

    def __init__(self, script: list[tuple[str, Any]]) -> None:
        self._script = script

    async def astream(
        self,
        payload: object,
        config: object = None,
        *,
        stream_mode: object = None,
    ) -> AsyncIterator[tuple[str, Any]]:
        _ = (payload, config, stream_mode)
        for item in self._script:
            yield item


def _final_state() -> dict[str, object]:
    return {
        "messages": [HumanMessage(content="hi"), AIMessage(content="أهلاً بك")],
        "retrieved_sources": [],
    }


def test_stage_events_then_done() -> None:
    async def _run() -> list[dict[str, object]]:
        graph = FakeStreamGraph(
            [
                ("updates", {"validate_request": {"intent": "greeting"}}),
                ("updates", {"answer": {"messages": []}}),
                ("values", _final_state()),
            ]
        )
        return [e async for e in stream_run(graph, {"messages": []}, {})]

    events = _run_sync(_run())
    assert [e["type"] for e in events] == ["stage", "stage", "done"]
    assert events[0]["node"] == "validate_request"
    assert events[1]["node"] == "answer"
    assert events[2]["state"] == _final_state()


def test_token_events_from_message_chunks() -> None:
    async def _run() -> list[dict[str, object]]:
        chunk = AIMessageChunk(content="مرحب")
        graph = FakeStreamGraph(
            [
                ("messages", (chunk, {"langgraph_node": "answer"})),
                ("values", _final_state()),
            ]
        )
        return [e async for e in stream_run(graph, {"messages": []}, {})]

    events = _run_sync(_run())
    assert events[0] == {"type": "token", "node": "answer", "text": "مرحب"}
    assert events[-1]["type"] == "done"


def test_empty_token_chunks_skipped() -> None:
    async def _run() -> list[dict[str, object]]:
        graph = FakeStreamGraph(
            [
                ("messages", (AIMessageChunk(content=""), {"langgraph_node": "answer"})),
                ("values", _final_state()),
            ]
        )
        return [e async for e in stream_run(graph, {"messages": []}, {})]

    events = _run_sync(_run())
    assert [e["type"] for e in events] == ["done"]


def test_non_answer_tokens_suppressed() -> None:
    from app.graph.streaming import stream_run as _stream_run

    async def _run() -> list[dict[str, object]]:
        graph = FakeStreamGraph(
            [
                ("messages", (AIMessageChunk(content='{"tool":1}'), {"langgraph_node": "quiz_agent"})),
                ("messages", (AIMessageChunk(content="مرحب"), {"langgraph_node": "answer"})),
                ("values", _final_state()),
            ]
        )
        return [e async for e in _stream_run(graph, {"messages": []}, {})]

    events = _run_sync(_run())
    tokens = [e for e in events if e["type"] == "token"]
    assert tokens == [{"type": "token", "node": "answer", "text": "مرحب"}]


def test_graph_error_becomes_error_event() -> None:
    class Boom:
        async def astream(
            self,
            payload: object,
            config: object = None,
            *,
            stream_mode: object = None,
        ) -> AsyncIterator[tuple[str, Any]]:
            _ = (payload, config, stream_mode)
            raise RuntimeError("down")
            yield  # type: ignore[misc]  # مولد خامل بعد الخطأ

    async def _run() -> list[dict[str, object]]:
        return [e async for e in stream_run(Boom(), {"messages": []}, {})]

    events = _run_sync(_run())
    assert len(events) == 1 and events[0]["type"] == "error"


def test_encode_sse_framing() -> None:
    frame = encode_sse({"type": "stage", "node": "answer"})
    assert frame.startswith("event: stage\n")
    assert frame.endswith("\n\n")
    assert '"node": "answer"' in frame or '"node":"answer"' in frame


def _run_sync(coro: Any) -> Any:
    import asyncio

    return asyncio.run(coro)


class ChunkedFake:
    """نموذج وهمي يبث قطعتين (يثبت التجميع في العقدة الحقيقية)."""

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        _ = (messages, callbacks)
        return AIMessage(content="مرحبا")

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = (messages, callbacks)
        yield "مرح"
        yield "با"

    def bind_tools(self, tools: Any) -> Any:
        _ = tools
        return self


def test_answer_node_accumulates_streamed_chunks() -> None:
    from app.graph.content import message_text
    from app.graph.nodes.answer import make_answer_node

    node = make_answer_node(ChunkedFake())  # type: ignore[arg-type]
    result = _run_sync(node({"messages": [HumanMessage(content="hi")]}))
    assert message_text(result["messages"][0].content) == "مرحبا"


def test_graph_token_events_end_to_end() -> None:
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langgraph.checkpoint.memory import InMemorySaver

    from app.graph.builder import build_graph
    from app.graph.content import message_text
    from tests.test_phase1 import FakeStructuredGeneral

    class LangchainBackedFake:
        """وهمي بخلفية runnable حقيقية: invoke متزامن + astream يمرر callbacks."""

        def __init__(self) -> None:
            self._llm = GenericFakeChatModel(messages=iter(["رد متدفق"]))

        def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
            _ = (messages, callbacks)
            return AIMessage(content="رد متدفق")

        async def astream(
            self, messages: list[BaseMessage], callbacks: Any = None
        ) -> AsyncIterator[str]:
            async for chunk in self._llm.astream(
                messages, config={"callbacks": callbacks or []}
            ):
                yield message_text(chunk.content)

        def bind_tools(self, tools: Any) -> Any:
            _ = tools
            return self

    graph = build_graph(
        LangchainBackedFake(), FakeStructuredGeneral(), [], checkpointer=InMemorySaver()  # type: ignore[arg-type]
    )

    async def _run() -> list[dict[str, object]]:
        return [
            e
            async for e in stream_run(
                graph,
                {"messages": [HumanMessage(content="hi")]},
                {"configurable": {"thread_id": "t1"}},
            )
        ]

    events = _run_sync(_run())
    texts = "".join(str(e["text"]) for e in events if e["type"] == "token")
    assert texts == "رد متدفق"
    assert events[-1]["type"] == "done"


def test_token_tapping_through_adapter_callbacks() -> None:
    """محول يمرر callbacks الإعداد لـ llm.astream ← وضع messages يلتقط الرموز."""
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.runnables import RunnableConfig
    from langgraph.graph import END, START, StateGraph
    from typing_extensions import TypedDict

    from app.graph.content import message_text

    class TappingAdapter:
        def __init__(self, llm: GenericFakeChatModel) -> None:
            self._llm = llm

        async def astream(
            self, messages: list[BaseMessage], callbacks: Any = None
        ) -> AsyncIterator[str]:
            async for chunk in self._llm.astream(
                messages, config={"callbacks": callbacks or []}
            ):
                yield message_text(chunk.content)

    class _S(TypedDict):
        messages: list[BaseMessage]

    async def _node(state: _S, config: RunnableConfig) -> dict[str, object]:
        adapter = TappingAdapter(GenericFakeChatModel(messages=iter(["hello world"])))
        parts: list[str] = []
        callbacks = config.get("callbacks")
        async for delta in adapter.astream(list(state["messages"]), callbacks=callbacks):
            parts.append(delta)
        return {"messages": [AIMessage(content="".join(parts))]}

    graph = StateGraph(_S)
    graph.add_node("answer", _node)
    graph.add_edge(START, "answer")
    graph.add_edge("answer", END)
    compiled = graph.compile()

    async def _run() -> list[dict[str, object]]:
        return [e async for e in stream_run(compiled, {"messages": []}, {})]

    events = _run_sync(_run())
    tokens = [e for e in events if e["type"] == "token"]
    assert tokens and "".join(str(t["text"]) for t in tokens) == "hello world"
    assert {t["node"] for t in tokens} == {"answer"}
    assert events[-1]["type"] == "done"
