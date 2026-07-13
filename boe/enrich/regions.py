"""Detección de comunidad autónoma y ámbito territorial.

Migrado de `app/services/boe_fetcher.py` a funciones puras (sin sesión de DB),
para poder testearlas de forma aislada. Devuelven nombres/enum; el mapeo a
filas de la tabla `regions` lo hace la capa de repositorio.
"""

from __future__ import annotations

import re

from boe.core.enums import Scope

# Regex por comunidad autónoma (nombre canónico → patrón).
REGION_REGEX: dict[str, str] = {
    "Andalucía": r"\b(andaluc[ií]a|junta de andaluc[ií]a)\b",
    "Aragón": r"\b(arag[oó]n|gobierno de arag[oó]n)\b",
    "Asturias": r"\b(asturias|principado de asturias)\b",
    "Islas Baleares": r"\b(illes balears|baleares|islas baleares)\b",
    "Canarias": r"\b(canarias|gobierno de canarias)\b",
    "Cantabria": r"\bcantabria\b",
    "Castilla-La Mancha": r"\bcastilla[- ]la mancha\b",
    "Castilla y León": r"\bcastilla y le[oó]n\b",
    "Cataluña": r"\b(catalu[ññ]a|catalunya)\b",
    "Comunidad Valenciana": r"\b(comunidad valenciana|generalitat valenciana)\b",
    "Extremadura": r"\bextremadura\b",
    "Galicia": r"\b(galicia|xunta de galicia)\b",
    "Madrid": r"\b(comunidad de madrid|madrid)\b",
    "Murcia": r"\b(murcia|servicio murciano de salud)\b",
    "Navarra": r"\b(navarra|comunidad foral de navarra)\b",
    "País Vasco": r"\b(pa[ií]s vasco|euskadi)\b",
    "La Rioja": r"\bla rioja\b",
    "Ceuta": r"\bceuta\b",
    "Melilla": r"\bmelilla\b",
}

_REGION_COMPILED = {name: re.compile(pat) for name, pat in REGION_REGEX.items()}

_EUROPE = re.compile(
    r"uni[oó]n europea|europe[oa]|reglamento \(ue\)|directiva \(ue\)|parlamento europeo"
)
_NATIONAL = re.compile(
    r"\b(estado|gobierno de espa[ñn]a|jefatura del estado|"
    r"bolet[ií]n oficial del estado)\b"
)
_ANY_REGION = re.compile("|".join(REGION_REGEX.values()))


def detect_regions(texto: str) -> list[str]:
    """Nombres de las CCAA mencionadas en el texto."""
    low = texto.lower()
    return [name for name, rx in _REGION_COMPILED.items() if rx.search(low)]


def detect_scope(texto: str) -> Scope:
    """Ámbito territorial del texto: europeo > nacional > autonómico > otro."""
    low = texto.lower()
    if _EUROPE.search(low):
        return Scope.EUROPEO
    if _NATIONAL.search(low):
        return Scope.NACIONAL
    if _ANY_REGION.search(low):
        return Scope.AUTONOMICO
    return Scope.OTRO
