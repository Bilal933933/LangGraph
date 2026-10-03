# تصميم الحالة (State Design) — المرحلة 2

## الحقول الأربعة

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: NotRequired[Intent]  # greeting | general_question | generate_quiz | unsupported
    quiz_request: NotRequired[QuizRequest]  # topic, grade_level, num_questions, question_types
    missing_fields: NotRequired[list[str]]  # أسماء النواقص فقط
```

## الكاتب والقارئ لكل حقل

| الحقل | الكاتب | القارئ | المخفض |
|-------|--------|--------|--------|
| `messages` | كل عقدة تضيف رسالتها | المصنف والنموذج والرد النهائي | `add_messages` يدمج بدل الاستبدال |
| `intent` | `classify` | `route_by_intent` | استبدال |
| `quiz_request` | `extract` | `confirm_ready` (والتوليد في المرحلة 3) | استبدال |
| `missing_fields` | `extract` | `route_after_extract` | استبدال |

## الرسائل والملكية

- رسالة المستخدم تدخل قبل `START` كـ `HumanMessage` عبر `ChatService.handle_message`.
- ردود العقد `AIMessage` (وأدوات لاحقا `ToolMessage`).
- المالك صفة على الرسالة (`name="answer"` …) لا حقل في الحالة.
- `message_text` في `app/graph/content.py` يستخرج النص للعرض ويتجاهل كتل التفكير.

## شرط التسلسل (للمرحلة 5)

- الحقول يجب أن تبقى قابلة لـ JSON لأن `Checkpointer` يسلسل اللقطات.
- لهذا نماذج Pydantic بسيطة بلا كائنات حية داخل الحالة.
