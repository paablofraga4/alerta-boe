"""Clasificación temática de publicaciones.

Primera pasada por regex (rápida, gratis, offline), migrada de
`app/services/classifier.py`. La clasificación semántica pesada
(`sentence-transformers`) del legacy se sustituye en el pipeline por una pasada
LLM opcional (`classify_with_llm`), que solo se usa si hay proveedor configurado.
"""

from __future__ import annotations

import re

# (patrón, categoría). Migrado del legacy, con las mismas categorías.
CATEGORIAS_REGEX: list[tuple[str, str]] = [
    (r"\bsubvencione?s?\b|\bayudas?\b|\bfondos europeos\b", "Subvención"),
    (r"\bnombramiento?s?\b|\bdesignaci[oó]n\b|\bceses?\b", "Empleo público"),
    (r"\boposiciones?\b|\bconcurso\b|\bbolsa de trabajo\b", "Empleo público"),
    (r"\bconvenios?\b|\bacuerdos internacionales?\b", "Convenio"),
    (r"\bsanciones?\b|\bmulta?s?\b|\bexpediente sancionador\b", "Sanción"),
    (r"\bsentencia\b|\btribunal\b|\bresoluci[oó]n judicial\b|\bjuzgado\b", "Sentencia"),
    (r"\bnormas?\b|\breglamentos?\b|\bleyes?\b|\bestatutos?\b", "Norma"),
    (r"\bplanes de estudios?\b|\benseñanza\b|\beducaci[oó]n\b|\bbecas?\b", "Educación"),
    (r"\bsalud\b|\bservicio(s)? de salud\b|\bespecialidades sanitarias\b", "Sanidad"),
    (r"\bmedio ambiente\b|\bimpacto ambiental\b|\benerg[ií]a renovable\b", "Medio ambiente"),
    (r"\bpresupuestos?\b|\bdeuda\b|\bimpuestos?\b|\bmercado de valores\b", "Economía"),
    (r"\binfraestructura(s)?\b|\btransporte\b|\bobras p[úu]blicas\b", "Infraestructura"),
    (r"\bagricultura\b|\bganado\b|\bpesca\b|\bPAC\b", "Agroalimentario"),
    (r"\btelecomunicaciones\b|\btelevisi[oó]n\b|\bTIC\b|\bdigital\b", "Tecnología"),
    (r"\bjusticia\b|\bprocedimientos judiciales?\b|\bletrados?\b", "Justicia"),
    (r"\bseguridad\b|\bdefensa\b|\bFuerzas Armadas\b", "Seguridad"),
    (r"\bbienes de inter[eé]s cultural\b|\bcultura\b|\bpatrimonio\b", "Cultura"),
    (r"\bigualdad\b|\bdiversidad\b|\binclusi[oó]n\b|\bdiscapacidad\b", "Asuntos sociales"),
    (r"\bempresas?\b|\baut[oó]nomos?\b|\bcomercio\b|\bemprendimiento\b", "Empresa y comercio"),
]

_COMPILED = [(re.compile(pat), cat) for pat, cat in CATEGORIAS_REGEX]

# Taxonomía completa (para pasarla como opciones al LLM).
TAXONOMY: list[str] = sorted({cat for _, cat in CATEGORIAS_REGEX})


def classify_by_regex(texto: str) -> list[str]:
    """Categorías detectadas por patrones. Vacío si ninguna coincide."""
    low = texto.lower()
    found: list[str] = []
    for rx, cat in _COMPILED:
        if rx.search(low) and cat not in found:
            found.append(cat)
    return found
