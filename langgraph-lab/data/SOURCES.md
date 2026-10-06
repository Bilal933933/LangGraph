# بيان مصادر المعرفة (داخلي — يُستكمل الترخيص من مالك البيانات)

## الحالة
- 165 ملف ماركداون (15MB): `textbook/` = 22 (كتب منهجية)، `references/` = 143 (مراجع).
- البنية: `{textbook|references}/{المرحلة}/{الصف أو المادة}/{المجلد}/part-NN.md` بعناوين `#`/`##`.
- ⚠️ الترخيص: غير موثق — لا تُعِد توزيع هذه الملفات خارج الفريق قبل توثيق مصدر كل كتاب وترخيصه هنا.

## معاملات الاستيعاب (ثابتة — أي تغيير يعيد بناء القاعدة كلها)
- التقطيع: `app/knowledge/chunking.py` — واعٍ لعناوين 1-3، `max_chars=2000`، تراكب 50 كلمة، حتمي.
- المعرف: `doc_key = sha256(المسار النسبي)` — إعادة التشغيل تستبدل بدل التكرار.
- التضمين: e5-small محلي (ONNX، بُعد 384) — المقاطع ببادئة `passage:` والأسئلة `query:`.
- النموذج عبر `LOCAL_EMBEDDING_PATH` (راجع `app/knowledge/embeddings.py`) — لا مسارات ثابتة في الكود.
- البحث النصي: `to_tsvector('simple', search_text)` — نفس إعداد الاستعلام في `pg_knowledge.py`.

## إعادة البناء
```powershell
cp .env.example .env   # DATABASE_URL يشير إلى Postgres فارغ
docker compose up -d db
uv run python scripts/ingest.py --dry-run   # تحقق أولًا: docs=165
uv run python scripts/ingest.py
```

## التحقق بعد الاستيعاب
```sql
SELECT count(*), count(DISTINCT doc_key) FROM knowledge_chunks;
-- docs=165 مميزة، chunks≈7757 (بتقطيع 2000/50)
SELECT book_id, count(*) FROM knowledge_chunks GROUP BY book_id ORDER BY 2 DESC;
```
