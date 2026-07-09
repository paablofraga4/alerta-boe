"""Cálculo de embeddings para la búsqueda semántica (pgvector).

`sentence-transformers` es pesado, así que se importa de forma perezosa: el
modelo solo se carga cuando de verdad se va a embeber (en el worker, extra
`[embeddings]`). Los tests y la API no lo necesitan.
"""

from __future__ import annotations

from functools import lru_cache

from boe.core.config import settings


@lru_cache
def _model():  # pragma: no cover - requiere el modelo pesado
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embeddings_model)


def embed_text(text: str) -> list[float]:  # pragma: no cover
    """Vector del texto, con la dimensión esperada por el esquema."""
    model = _model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_document_text(title: str, full_text: str | None) -> list[float]:  # pragma: no cover
    """Embedding representativo del documento (título + inicio del cuerpo)."""
    payload = title if not full_text else f"{title}\n\n{full_text[:2000]}"
    return embed_text(payload)
