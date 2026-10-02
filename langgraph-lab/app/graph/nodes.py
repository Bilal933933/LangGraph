"""العقد (Nodes = دوال المعالجة داخل الرسم)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from app.domain.ports import ChatModelPort
from app.domain.state import ChatState


def classify_node(state: ChatState) -> dict[str, list[BaseMessage]]:
    """العقدة 1: تصنيف شكلي (المرحلة 1 تمرير فقط).

    المرحلة 2 ستضيف توجيهاً شرطياً هنا. الآن نعيد تحديثاً فارغاً
    لإثبات مفهوم العقدة دون تغيير الحالة.
    """
    _ = state  # موضع التوسعة في المرحلة 2
    return {}


def make_answer_node(
    model: ChatModelPort,
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """مصنع العقدة 2: يغلق (Closure) على النموذج المحقون."""

    def _answer(state: ChatState) -> dict[str, list[BaseMessage]]:
        text = model.invoke(list(state["messages"]))
        return {"messages": [AIMessage(content=text)]}

    return _answer
