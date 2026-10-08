# تصميم اللقطات (Checkpointer Design) — منفذ حاليًا

## القرارات (الحالية في `app/graph/checkpoints.py` + `app/main.py`)

- **الإنتاج**: `PostgresSaver` على نفس قاعدة بيانات العمل عبر `postgres_checkpointer_cm()` + `setup_postgres_tables()`.
- **التطوير**: `InMemorySaver` عبر `create_checkpointer()` بتخزين `lru_cache` عند غياب `DATABASE_URL` — تُفقد عند إعادة التشغيل.
- **الاختيار**: `resolve_checkpointer()` في `app/api/routes.py` — فارغ = ذاكرة، غير فارغ = Postgres حي واحد لعمر العملية، يُغلق بـ `close_checkpointer()`.
- **الخيط**: `thread_id = f"t{user_id}:c{conversation_id}"` عبر `ChatService.thread_id_for_conversation` — يعزل محادثة عن أخرى.
- **التوقيت**: لقطة بعد كل عقدة (بعد دمج المخفضات)، والقراءة عند `invoke` بنفس `thread_id`.
- **الحماية**: `recursion_limit = MAX_STEPS = 12` ضد الحلقات اللانهائية.
- **الفصل**: جداول التطبيق (`Teacher/Conversation/Message`) ننشئها عبر SQLAlchemy، وجداول اللقطات (`checkpoints/checkpoint_writes/checkpoint_blobs/checkpoint_migrations`) ينشئها `PostgresSaver.setup()` ولا نلمسها يدويًا.

## الربط الحالي

| الملف | الدور |
|-------|-------|
| `app/graph/checkpoints.py` | `create_checkpointer()` + `postgres_checkpointer_cm()` + `setup_postgres_tables()` + `normalize_postgres_url()` |
| `app/graph/builder.py` | `build_graph(..., checkpointer)` ← `compile(checkpointer=...)`، فارغ = بلا حفظ |
| `app/api/routes.py` | `resolve_checkpointer()` + `close_checkpointer()` + `get_chat_service()` |
| `app/api/conversations.py` | `get_conversation_graph()` بنفس المحلل (تكرار يُوحّد لاحقًا) |
| `app/main.py` | `lifespan`: `create_tables()` + `setup_postgres_tables()` عند البدء، إغلاق نظيف عند الإيقاف |
| `app/services/chat_service.py` | `handle_message(message, thread_id, teacher_id)` للاستئناف |
| `app/services/conversation_service.py` | `send_message_detail()` يبني `thread` من المالك ثم `invoke` |

## الشروط المحققة

- كل حقول `ChatState` قابلة لـ JSON — انظر `docs/state-design.md`.
- `Interrupt` للموافقة البشرية مؤجل — البنية جاهزة له لأنه يتطلب نفس الحافظ.
