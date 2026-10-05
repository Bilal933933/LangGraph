"""تضمين الأسئلة محلياً (e5-small عبر ONNX — نفس نموذج المقاطع المخزنة).

بروتوكول e5: الأسئلة تُسبق بـ `query:` والمقاطع خُزنت بـ `passage:`.
التحميل كسول مرة واحدة (Singleton) عند أول سؤال فقط.
"""

import os
import threading
from typing import Any

MODEL_DIR = os.getenv(
    "LOCAL_EMBEDDING_PATH", r"D:\Offline-600GB\07-RAG\models\e5-small\onnx"
)
MODEL_FILE = os.getenv("LOCAL_EMBEDDING_MODEL", "model_O4.onnx")
MODEL_DIM = 384
QUERY_PREFIX = "query: "
MAX_LENGTH = 512

_lock = threading.Lock()
_session: Any = None
_tokenizer: Any = None


def _load() -> None:
    """تحميل النموذج والمجزئ مرة واحدة (آمن للخيوط)."""
    global _session, _tokenizer
    with _lock:
        if _session is not None:
            return
        import onnxruntime as ort  # type: ignore[import-untyped]
        from tokenizers import Tokenizer

        model_path = os.path.join(MODEL_DIR, MODEL_FILE)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"نموذج التضمين غير موجود: {model_path}")
        tok_path = os.path.join(MODEL_DIR, "tokenizer.json")
        _tokenizer = Tokenizer.from_file(tok_path)
        _session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])


def embed_query(text: str) -> list[float]:
    """سؤال ← متجه 384 مُطبّع. فارغ ← خطأ ValueError."""
    import numpy as np

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("نص السؤال فارغ.")
    _load()
    assert _session is not None and _tokenizer is not None
    encoded = _tokenizer.encode(QUERY_PREFIX + cleaned[:2000])
    ids = encoded.ids[:MAX_LENGTH]
    mask = encoded.attention_mask[:MAX_LENGTH]
    inputs = {
        "input_ids": np.array([ids], dtype=np.int64),
        "attention_mask": np.array([mask], dtype=np.int64),
        "token_type_ids": np.zeros((1, len(ids)), dtype=np.int64),
    }
    hidden = np.array(_session.run(["last_hidden_state"], inputs)[0])
    weights = np.array(mask, dtype=np.float64).reshape(1, -1, 1)
    summed = (hidden * weights).sum(axis=1)
    counts = weights.sum(axis=1).clip(min=1e-9)
    vec = (summed / counts)[0]
    norm = float(np.linalg.norm(vec))
    if norm < 1e-12:
        raise ValueError("تعذر تضمين السؤال.")
    vec = vec / norm
    if vec.shape[0] != MODEL_DIM:
        raise ValueError(f"بُعد غير متوقع: {vec.shape[0]}")
    return [float(x) for x in vec.tolist()]
