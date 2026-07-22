"""Triaje editorial: categoría y relevancia ciudadana de cada publicación.

El ~70% del BOE diario es ruido para un ciudadano (nombramientos, edictos,
anuncios). Esta etapa, determinista y sin coste LLM, clasifica cada publicación
por su metadato de sumario (sección, epígrafe, título, rango) en una categoría
editorial y le asigna una relevancia 0-100. La portada usa ambas para enseñar
primero lo que importa y colapsar el resto.

Secciones oficiales del BOE:
  1  Disposiciones generales      → normas (lo jurídicamente importante)
  2A Nombramientos                → ruido
  2B Oposiciones y concursos      → oposiciones
  3  Otras disposiciones          → aquí está el dinero (ayudas) entre trámite
  4  Administración de Justicia   → ruido (edictos)
  5  Anuncios                     → ruido (licitaciones interesan a empresas)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Categorías editoriales. Las tres primeras son "valor"; el resto, colapsable.
CAT_NORMAS = "normas"
CAT_AYUDAS = "ayudas"
CAT_OPOSICIONES = "oposiciones"
CAT_OTRAS = "otras"
CAT_NOMBRAMIENTOS = "nombramientos"
CAT_JUSTICIA = "justicia"
CAT_ANUNCIOS = "anuncios"

CATEGORY_LABEL: dict[str, str] = {
    CAT_NORMAS: "Leyes y normas",
    CAT_AYUDAS: "Ayudas, becas y subvenciones",
    CAT_OPOSICIONES: "Oposiciones y empleo público",
    CAT_OTRAS: "Otras disposiciones",
    CAT_NOMBRAMIENTOS: "Nombramientos y ceses",
    CAT_JUSTICIA: "Edictos y justicia",
    CAT_ANUNCIOS: "Contratación y anuncios",
}

# Categorías que la portada colapsa en una sola línea con recuento.
NOISE_CATEGORIES = {CAT_NOMBRAMIENTOS, CAT_JUSTICIA, CAT_ANUNCIOS}

_BASE_RELEVANCE = {
    CAT_AYUDAS: 85,
    CAT_NORMAS: 75,
    CAT_OPOSICIONES: 65,
    CAT_OTRAS: 35,
    CAT_ANUNCIOS: 15,
    CAT_NOMBRAMIENTOS: 10,
    CAT_JUSTICIA: 8,
}

_RX_AYUDAS = re.compile(
    r"\bsubvencion|\bayudas?\b|\bbecas?\b|\bpremios?\b|bono\b|\bprestacion", re.I
)
_RX_OPOSICIONES = re.compile(
    r"oposicion|\bconcurso\b|proceso selectivo|bolsa de trabajo|\bplazas?\b", re.I
)
_RX_NOMBRAMIENTOS = re.compile(r"\bnombra|\bcesa|\bcese\b|\bdispone el cese|\bdesigna", re.I)
# Señales de impacto directo en el bolsillo/vida del ciudadano.
_RX_BOOST = re.compile(
    r"salario minimo|\birpf\b|\biva\b|pensione?s|alquiler|hipotec|autonomo|"
    r"\bplazo\b|convocatoria|calendario|festivos|\bdana\b|emergencia",
    re.I,
)
_RANGOS_FUERTES = ("ley", "real decreto-ley", "real decreto legislativo")


@dataclass(frozen=True)
class Triage:
    category: str
    relevance: int  # 0-100

    @property
    def noise(self) -> bool:
        return self.category in NOISE_CATEGORIES


def _normalize(text: str | None) -> str:
    return (text or "").lower()


def triage(
    *,
    title: str,
    seccion_codigo: str | None,
    epigrafe: str | None = None,
    rango: str | None = None,
) -> Triage:
    """Clasifica una publicación por sus metadatos de sumario."""
    titulo = _normalize(title)
    epi = _normalize(epigrafe)
    sec = (seccion_codigo or "").strip().upper()

    category = _category(titulo, epi, sec)
    relevance = _BASE_RELEVANCE.get(category, 20)

    # Boosts acotados: señales de dinero/plazo/impacto en el título.
    if category not in NOISE_CATEGORIES:
        if _RX_BOOST.search(titulo):
            relevance += 12
        if _RX_AYUDAS.search(titulo) and category != CAT_AYUDAS:
            relevance += 8
    rango_l = _normalize(rango)
    if any(rango_l.startswith(r) for r in _RANGOS_FUERTES):
        relevance += 10

    return Triage(category=category, relevance=max(0, min(relevance, 100)))


def _category(titulo: str, epi: str, sec: str) -> str:
    # Sección manda; el epígrafe/título desambigua dentro de ella.
    if sec == "1":
        return CAT_NORMAS
    if sec == "2":
        if _RX_OPOSICIONES.search(epi) or _RX_OPOSICIONES.search(titulo):
            return CAT_OPOSICIONES
        return CAT_NOMBRAMIENTOS
    if sec == "4":
        return CAT_JUSTICIA
    if sec == "5":
        return CAT_ANUNCIOS
    # Sección 3 (y desconocidas): separar el dinero del trámite.
    if _RX_AYUDAS.search(epi) or _RX_AYUDAS.search(titulo):
        return CAT_AYUDAS
    if _RX_OPOSICIONES.search(epi) or _RX_OPOSICIONES.search(titulo):
        return CAT_OPOSICIONES
    if _RX_NOMBRAMIENTOS.search(titulo):
        return CAT_NOMBRAMIENTOS
    return CAT_OTRAS
