"""محولات Gemini (تنفيذ المنافذ، بلا منطق رسم)."""

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.core.errors import AppError, ErrorCode
from app.domain.ports import ChatModelPort
from app.graph.content import message_text


class GeminiChatModel:
    """محول Gemini يحقق عقد ChatModelPort (SOLID: عكس الاعتماد)."""

    def __init__(self, api_key: str, model_name: str, tools: list[BaseTool] | None = None) -> None:
        self._api_key = api_key
        self._model_name = model_name
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        self._llm = llm.bind_tools(tools) if tools else llm

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        result = self._llm.invoke(messages, config={"callbacks": callbacks or []})
        text = message_text(result.content)
        tool_calls = list(result.tool_calls or [])
        return AIMessage(content=text, tool_calls=tool_calls)

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        """يبث عبر Runnable مع تمرير callbacks ليلتقطها وضع messages."""
        from langchain_core.runnables import RunnableConfig

        config: RunnableConfig = {"callbacks": callbacks or []}
        async for chunk in self._llm.astream(messages, config=config):
            yield message_text(chunk.content)

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        """يربط الأدوات ← محول جديد بأدوات مربوطة."""
        return GeminiChatModel(api_key=self._api_key, model_name=self._model_name, tools=tools)


class GeminiStructuredModel:
    """محول المخرجات المهيكلة عبر with_structured_output."""

    def __init__(self, api_key: str, model_name: str) -> None:
        self._llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)

    def parse(self, messages: list[BaseMessage], schema: type[BaseModel]) -> Any:
        try:
            structured = self._llm.with_structured_output(schema)
            result = structured.invoke(messages)
        except Exception as exc:
            raise AppError(ErrorCode.LLM_FAILED, "فشل استدعاء النموذج.", details=str(exc)) from exc
        if isinstance(result, schema):
            return result
        if isinstance(result, dict):
            try:
                return schema.model_validate(result)
            except Exception as exc:
                raise AppError(ErrorCode.INVALID_MODEL_OUTPUT, "مخرجات النموذج غير صالحة.") from exc
        raise AppError(ErrorCode.INVALID_MODEL_OUTPUT, "مخرجات النموذج غير صالحة.")
