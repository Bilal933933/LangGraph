# تصميم اللقطات (Checkpointer Design) — تصميم أولي

> لا تنفيذ بعد. يطبق في مرحلة الذاكرة والموافقة (المرحلة 5).

## القرارات

- **المحرك للإنتاج**: `AsyncPostgresSaver` على نفس قاعدة بيانات العمل.
- **التطوير**: `MemorySaver` (أو ملف) عند غياب `postgres_dsn` — بلا إعداد.
- **نسخة واحدة مشتركة**: مصنع بتخزين مؤقت (`lru_cache`) يمرر لـ `compile(checkpointer=...)`.
- **الخيط**: `thread_id` لكل محادثة (معلم + جلسة) يرافق كل `invoke`.
- **التوقيت**: لقطة بعد كل عقدة (بعد دمج المخفضات)، والقراءة مرة عند الاستئناف.
- **الحماية**: `recursion_limit` ضد الحلقات اللانهائية + تنظيف دوري للخيوط القديمة.

## الربط المقترح

| الملف | التعديل |
|-------|---------|
| `app/core/config.py` | إضافة `postgres_dsn` (فارغ = وضع التطوير) |
| `app/graph/checkpoints.py` | جديد: `create_checkpointer(settings)` يختار حسب البيئة |
| `app/graph/builder.py` | `compile(checkpointer=...)` بدل التجميع الحالي |
| `app/main.py` | تهيئة جداول اللقطات وإغلاق الاتصال في `lifespan` |
| `app/services/chat_service.py` | `handle_message(message, thread_id)` للاستئناف |

## الشروط المسبقة (محققة)

- حقول `ChatState` الأربعة قابلة لـ JSON — انظر `docs/state-design.md`.
- لا تغيير على العقد والحواف؛ اللقطات طبقة ربط فقط.
- `Interrupt` للموافقة البشرية يأتي مع نفس المرحلة لأنه يتطلب الحافظ.
