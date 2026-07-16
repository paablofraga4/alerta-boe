"""Parseo de fechas en español extraídas por el agente ("1 de agosto de 2026").

Los plazos del brief (`structured.plazos[].fecha`) vienen en texto libre tal
como aparecen en la norma. Aquí se convierten a `date` cuando es posible, para
poder ordenarlos por urgencia en el Radar. Lo que no se puede fechar con
seguridad (p. ej. "3 meses desde la publicación") se descarta del radar: mejor
no mostrar una cuenta atrás inventada.
"""

from __future__ import annotations

import re
from datetime import date

_MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

# "1 de agosto de 2026", "30 de septiembre", "hasta el 15 de enero de 2027"
_RX_LARGA = re.compile(
    r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)(?:\s+de\s+(\d{4}))?", re.IGNORECASE
)
# "30/09/2026", "30-09-2026"
_RX_NUMERICA = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})")
# ISO "2026-09-30"
_RX_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def parse_fecha_es(texto: str, *, referencia: date) -> date | None:
    """Extrae una fecha concreta de un texto en español; None si no la hay.

    Si el texto no trae año, se asume el de `referencia` (fecha de publicación
    de la norma) y, si el resultado ya quedó atrás, el año siguiente — los
    plazos siempre miran hacia delante desde la publicación.
    """
    if not texto:
        return None

    m = _RX_ISO.search(texto)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _safe_date(y, mo, d)

    m = _RX_NUMERICA.search(texto)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _safe_date(y, mo, d)

    m = _RX_LARGA.search(texto)
    if m:
        d = int(m.group(1))
        mes = _MESES.get(m.group(2).lower())
        if mes is None:
            return None
        if m.group(3):
            return _safe_date(int(m.group(3)), mes, d)
        # Sin año: el de la publicación, o el siguiente si ya pasó.
        candidata = _safe_date(referencia.year, mes, d)
        if candidata and candidata < referencia:
            candidata = _safe_date(referencia.year + 1, mes, d)
        return candidata

    return None


def _safe_date(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None
