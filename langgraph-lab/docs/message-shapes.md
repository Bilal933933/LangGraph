# الأشكال الأربعة (مرجع مصحح) — `langgraph 1.2.12` + `langchain-core 1.6.6`

> القاعدة: `Message ≠ Request ≠ State ≠ Checkpoint ≠ Context`.
> عمود `النوع`: `حقيقي` = بنية فعلية من المكتبة/الكود، `توضيحي` = مثال للتوثيق فقط.

## 1. رسالة المستخدم بعد الهندلة (حقيقي)

الدخل الخارجي (`app/api/schemas.py`):
```json
{"message": "...", "thread_id": "default"}
```

داخل `ChatService._run_args` (`app/services/chat_service.py`):
`{"messages": [HumanMessage(content="...")]}` — لحظة الإنشاء `id=None` (مؤكد بالتنفيذ).

`model_dump()` الحقيقي:
```json
{"content": "...", "additional_kwargs": {}, "response_metadata": {}, "type": "human", "name": null, "id": null}
```
- `id` يولده مخفض `add_messages` لاحقًا كـ UUID — أي `msg-abc123` في الأمثلة توضيحي.
- `AIMessage` يضيف حقيقيًا: `tool_calls, invalid_tool_calls, usage_metadata`.
- لا يوجد `example: false` في `1.6.6`.
- `response_metadata` حسب المزود (Gemini: `model_name/finish_reason/safety_ratings`) — أي `{"model": ...}` توضيحي.

## 2. الحالة `ChatState` (حقيقي للبنية، توضيحي للقيم)

التعريف (`app/domain/state.py`): `messages: Annotated[list[BaseMessage], add_messages]` + حقول `NotRequired` (هوية/طلب/تنفيذ).
- `retrieved_sources`: overwrite كل دور (بلا reducer) + `text[:1500]` + `limit=5` — تضخم محدود (~7.5k حرف/لقطة). التخفيف المقترح: IDs فقط أو تفريغ بعد الدمج.
- `plan_sections`: التصفير موجود فعلًا (`plan_extract` يعيد `[]` + `_append_sections` يهمل القديم) — لا تسرب بين الطلبات.

## 3. التشيكبوينتر (حقيقي للبنية)

الإدخال العادي (حقيقي):
```json
{"configurable": {"thread_id": "t7:c12"}, "recursion_limit": 12}
```
- `checkpoint_ns/checkpoint_id` للـ time-travel فقط، لا للإدخال العادي.
- `thread_id` المسجلين: `t{user_id}:c{conversation_id}` مشتق server-side بعد فحص الملكية (`conversation_service.py`). الضيوف: `g:{ip}:{sha256(ip|raw)[:12]}` عزل best-effort ضد التصادم (الـ IP غير موثوق خلف proxy) — انظر §5.

اللقطة `CheckpointTuple` (حقيقي للبنية، توضيحي للقيم):
- `Checkpoint.v = 1` في `1.2.12` (نص السورس: `Currently 1`).
- `channel_versions`: نصوص مرتبة لا أعداد. `versions_seen: dict[node_id, versions]` مملوء لا `{}`.
- `pending_writes` موجود. الكبيرة (`messages`) في `checkpoint_blobs` وتعود `deserialized` لا `JSON`.
- الجداول 4: `checkpoints, checkpoint_writes, checkpoint_blobs, checkpoint_migrations`.

## 4. نافذة السياق (حقيقي للآلية)

- `select_window(messages, 20)` تقليم لحظي قبل كل `invoke` فقط — الأرشيف (`Message` + Checkpointer) بلا سقف ولا حذف أبدًا.
- الأمان: تُسقط الرسائل القائدة غير البشرية حتى أول `human` حتى لا تبدأ النافذة بـ `ai/tool` ولا تُيتّم `ToolMessage` عن `AIMessage(tool_calls)` — مطلوب لـ Gemini.
- أي شكل `{full_history, window, dropped}` توضيحي للتوثيق فقط.
