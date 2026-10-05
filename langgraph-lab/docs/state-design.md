# تصميم الحالة (State Design) — الحالي

## الحقول (13 حقلًا في `app/domain/state.py`)

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    teacher_id: NotRequired[int | None]
    intent: NotRequired[Intent]  # greeting | general_question | generate_quiz | plan_lesson | unsupported | update_profile
    quiz_request: NotRequired[QuizRequest]
    missing_fields: NotRequired[list[str]]
    pending_profile_name: NotRequired[str | None]
    profile_snapshot: NotRequired[dict[str, object]]  # {name, subject, grades}
    pending_profile: NotRequired[dict[str, object] | None]
    retrieved_sources: NotRequired[list[dict[str, object]]]
    lesson_request: NotRequired[LessonRequest]
    section_task: NotRequired[str | None]
    plan_sections: NotRequired[Annotated[list[dict], _append_sections]]
    plan_draft: NotRequired[LessonPlan]
```

## الكاتب والقارئ لكل حقل

| الحقل | الكاتب | القارئ | المخفض |
|-------|--------|--------|--------|
| `messages` | كل عقدة تضيف رسالتها + `ChatService` يحقن `HumanMessage` | المصنف والنموذج والرد النهائي | `add_messages` يدمج بدل الاستبدال |
| `teacher_id` | `ChatService` / `conversation_service` من المصادقة | `load_profile`, `apply_profile`, `save_profile` | استبدال |
| `intent` | `classify` | `route_by_intent` | استبدال |
| `quiz_request` | `extract` | `route_after_extract`, `confirm_ready` | استبدال |
| `lesson_request` | `plan_extract` (يدمج مع السابق) | `plan_retrieve`, `plan_section`, `plan_merge` | استبدال |
| `missing_fields` | `extract` / `plan_extract` | `route_after_extract`, `route_after_plan_extract`, `build_plan_clarification` | استبدال |
| `profile_snapshot` | `load_profile` / `apply_profile` | `apply_profile`, `build_plan_clarification`, موجهات الإجابة | استبدال |
| `pending_profile` | `extract_profile_info` | `apply_profile` | استبدال |
| `pending_profile_name` | `extract_profile` | `route_after_profile_extract`, `save_profile` | استبدال |
| `retrieved_sources` | `plan_retrieve` (+ `answer` للقراءة) | `plan_section`, `plan_merge`, API للعرض | استبدال |
| `section_task` | `plan_dispatch` عبر `Send` | `plan_section` | استبدال |
| `plan_sections` | عمال `plan_section` المتوازيون | `plan_merge` | `_append_sections` يدمج بلا فقد |
| `plan_draft` | `plan_merge` | API / الاختبارات | استبدال |

## قواعد الهوية مقابل السياق

- الحالة تحمل الهوية فقط (`teacher_id`)، والتفاصيل (`name, subject, grades`) تُجلب من `TeacherProfilePort` عند الحاجة.
- `profile_snapshot` cache للدور الحالي فقط، لا بديل دائم عن `teachers` + `teacher_grades`.
- أي حقل جديد يُضاف كـ `NotRequired` فقط عند ظهور ميزة تحتاجه.

## الرسائل والملكية

- رسالة المستخدم تدخل قبل `START` كـ `HumanMessage` عبر `ChatService.handle_message` / `conversation_service.send_message_detail`.
- ردود العقد `AIMessage` (وأدوات لاحقا `ToolMessage`).
- `message_text` في `app/graph/content.py` يستخرج النص للعرض ويتجاهل كتل التفكير.
- جدول `Message` للعرض فقط، لا يُعاد حقنه في الرسم وإلا تضاعف مع `add_messages`.

## شرط التسلسل

- الحقول يجب أن تبقى قابلة لـ JSON لأن `Checkpointer` يسلسل اللقطات.
- لهذا نماذج Pydantic بسيطة (`QuizRequest`, `LessonRequest`, `LessonPlan`) بلا كائنات حية داخل الحالة.
