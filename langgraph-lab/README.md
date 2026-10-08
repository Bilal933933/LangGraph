# مساعد المعلم — LangGraph + Gemini

وكيل تعليمي عربي: اختبارات، تحضير دروس، ملف معلم، بحث معرفي (RAG نصي/هجين
pgvector)، بحث ويب اختياري، ومحادثات محفوظة في Postgres.

## المكونات

- `app/` — FastAPI + LangGraph (نقاط: `/auth`، `/chat`، `/conversations`، وبث SSE في `streams.py`)
- `migrations/` — ترحيلات Alembic لجداول التطبيق (الإقلاع يرقّي حتى `head`)
- `scripts/ingest.py` — استيعاب `data/*.md` إلى `knowledge_chunks` (البيان في `data/SOURCES.md`)
- `tests/evals/` — الذهبي + فحوصات هيكلية للاختبارات والخطط (الحي بـ `RUN_LIVE_EVALS=1`)
- `web/` — واجهة Next.js (عربي RTL، ثيمات، TanStack Query + Zustand + sonner، إرسال متدفق)
- `app/graph/prompts/PROMPT_RULES.md` — قواعد هندسة البرومبتات الملزمة (القالب، الممنوعات، الذهبي)
- `docker-compose.yml` — Postgres 16 فقط (الأسرار من `.env`، لا قيم ثابتة)

## الأمان والحدود

- الجلب الخارجي لمضيف عام فقط (`fetch_guard`)، والسياق الخارجي موسوم كبيانات لا تعليمات.
- حدود المعدل: `CHAT_RPM` / `CHAT_GUEST_RPM` / `AUTH_RPM` (طلب/دقيقة).
- سقف الرموز اليومي `DAILY_TOKEN_CAP` لكل مستخدم/ضيف (`0` = بلا سقف) — يُفحص قبل الرسم ويُحاسَب بعده.

## التشغيل

```powershell
cp .env.example .env   # ثم ضع GOOGLE_API_KEY وPOSTGRES_PASSWORD وJWT_SECRET
docker compose up -d db
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 5003   # http://127.0.0.1:5003
```

الواجهة في نافذة ثانية:

```powershell
cd web
npm install
npm run dev   # http://127.0.0.1:3006 (يجب أن يكون ضمن CORS_ORIGINS)
```

ترحيل صريح (اختياري — الإقلاع يرحّل تلقائياً):

```powershell
uv run alembic -c alembic.ini upgrade head
```

## الفحوصات

```powershell
uv run ruff check app tests migrations
uv run mypy app
uv run pytest -q
```

```powershell
cd web; npx eslint .; npx tsc --noEmit
```

## ملاحظات

- `DATABASE_URL` فارغ = يعمل API بلا DB (وضع محدود)؛ مع Postgres تُفعّل
  المحادثات واللقطات والمعرفة.
- `create_tables` للاختبار والسكربتات فقط — الإنتاج عبر `migrations/`.
- السجلات محلية في `logs/` ولا تُرفع (راجع `.gitignore`).
