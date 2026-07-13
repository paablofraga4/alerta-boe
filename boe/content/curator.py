"""Curador: puntúa las publicaciones del día por 'interés general'.

Heurística transparente y testeable (sin LLM): premia el alcance (ámbito),
el rango normativo, los temas que tocan el bolsillo de la gente y el tamaño del
hilo de referencias (una norma muy conectada suele ser relevante). El resultado
alimenta la selección de qué publicar en redes.
"""

from __future__ import annotations

from dataclasses import dataclass

from boe.core.enums import Scope

# Temas de alto interés ciudadano (peso extra).
_HIGH_INTEREST_TOPICS = {
    "Subvención",
    "Economía",
    "Empresa y comercio",
    "Sanidad",
    "Educación",
    "Empleo público",
    "Asuntos sociales",
}

_SCOPE_WEIGHT = {
    Scope.EUROPEO: 0.9,
    Scope.NACIONAL: 1.0,
    Scope.AUTONOMICO: 0.6,
    Scope.OTRO: 0.2,
}

# Rangos normativos con más impacto (coincidencia por substring en minúsculas).
_RANGO_WEIGHT = [
    ("ley orgánica", 1.0),
    ("real decreto-ley", 1.0),
    ("ley", 0.9),
    ("real decreto", 0.8),
    ("orden", 0.5),
    ("resolución", 0.3),
]


@dataclass
class CandidateSignals:
    """Señales de un documento para puntuarlo (desacoplado del ORM)."""

    boe_id: str
    scope: Scope
    rango: str | None
    topics: list[str]
    n_references: int
    has_summary: bool


def _rango_score(rango: str | None) -> float:
    if not rango:
        return 0.2
    low = rango.lower()
    for needle, weight in _RANGO_WEIGHT:
        if needle in low:
            return weight
    return 0.3


def score(signals: CandidateSignals) -> float:
    """Puntuación de interés en [0, 1]."""
    scope = _SCOPE_WEIGHT.get(signals.scope, 0.2)
    rango = _rango_score(signals.rango)
    topic_hits = len(set(signals.topics) & _HIGH_INTEREST_TOPICS)
    topic = min(topic_hits / 2, 1.0)
    connectivity = min(signals.n_references / 8, 1.0)
    summary = 1.0 if signals.has_summary else 0.0

    # Media ponderada. El ámbito y el tema mandan; el hilo y el rango afinan.
    raw = (
        0.30 * scope
        + 0.25 * topic
        + 0.20 * rango
        + 0.15 * connectivity
        + 0.10 * summary
    )
    return round(raw, 4)


def rank(candidates: list[CandidateSignals], *, top_n: int = 3) -> list[tuple[CandidateSignals, float]]:
    """Ordena los candidatos por interés y devuelve los mejores con su score."""
    scored = [(c, score(c)) for c in candidates]
    scored.sort(key=lambda cs: cs[1], reverse=True)
    return scored[:top_n]
