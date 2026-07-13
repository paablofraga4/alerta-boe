"""Cliente de legislación consolidada del BOE.

Base: `GET /legislacion-consolidada` y sus sub-recursos por id:
  - `/id/{id}/metadatos`      → metadatos de la norma
  - `/id/{id}/texto/indice`   → índice (bloques/artículos)
  - `/id/{id}/analisis`       → materias, notas y **referencias** (el grafo)

El bloque `analisis` es el que habilita "el hilo y los precedentes": sus
`referencias.anteriores` y `referencias.posteriores` se traducen a aristas.
"""

from __future__ import annotations

from boe.clients.base import BOEHttpClient, as_list
from boe.clients.dto import ConsolidatedMeta, IndexBlock, ReferenceEntry
from boe.core.enums import ReferenceDirection, ReferenceType


def _texto(value: object) -> str | None:
    """Extrae `.texto` de los objetos `{codigo, texto}` típicos del BOE."""
    if isinstance(value, dict):
        return value.get("texto")
    if isinstance(value, str):
        return value
    return None


def parse_meta(payload: dict) -> ConsolidatedMeta | None:
    data = as_list(payload.get("data"))
    if not data:
        return None
    m = data[0]
    return ConsolidatedMeta(
        consolidated_id=m.get("identificador", ""),
        title=m.get("titulo", ""),
        rango=_texto(m.get("rango")),
        departamento=_texto(m.get("departamento")),
        ambito=_texto(m.get("ambito")),
        estado=_texto(m.get("estado_consolidacion")),
        fecha_disposicion=m.get("fecha_disposicion"),
        fecha_publicacion=m.get("fecha_publicacion"),
        fecha_vigencia=m.get("fecha_vigencia"),
        vigente=m.get("vigencia_agotada", "N") == "N",
        url_html=m.get("url_html_consolidada"),
    )


def parse_index(payload: dict) -> list[IndexBlock]:
    data = as_list(payload.get("data"))
    if not data:
        return []
    bloques = as_list(data[0].get("bloque"))
    result: list[IndexBlock] = []
    for b in bloques:
        block_id = b.get("id")
        if not block_id:
            continue
        result.append(
            IndexBlock(
                block_id=block_id,
                title=b.get("titulo", ""),
                fecha_actualizacion=b.get("fecha_actualizacion"),
                url=b.get("url"),
            )
        )
    return result


def _parse_ref_entries(raw_refs: object, direction: ReferenceDirection) -> list[ReferenceEntry]:
    entries: list[ReferenceEntry] = []
    for ref in as_list(raw_refs):
        if not isinstance(ref, dict):
            continue
        # La "palabra" de relación llega bajo distintas claves según el recurso.
        rel_text = (
            _texto(ref.get("palabra"))
            or _texto(ref.get("tipo"))
            or _texto(ref.get("relacion"))
        )
        entries.append(
            ReferenceEntry(
                target_boe_id=ref.get("referencia") or ref.get("id_norma"),
                target_title=ref.get("texto") or ref.get("titulo"),
                rel_type=ReferenceType.from_boe(rel_text),
                direction=direction,
                raw_text=rel_text,
            )
        )
    return entries


def parse_references(payload: dict) -> list[ReferenceEntry]:
    """Extrae las aristas del grafo del bloque `analisis`."""
    data = as_list(payload.get("data"))
    if not data:
        return []
    analisis = data[0].get("analisis") or {}
    referencias = analisis.get("referencias") or {}

    entries: list[ReferenceEntry] = []
    entries += _parse_ref_entries(referencias.get("anterior"), ReferenceDirection.ANTERIOR)
    entries += _parse_ref_entries(referencias.get("anteriores"), ReferenceDirection.ANTERIOR)
    entries += _parse_ref_entries(referencias.get("posterior"), ReferenceDirection.POSTERIOR)
    entries += _parse_ref_entries(referencias.get("posteriores"), ReferenceDirection.POSTERIOR)
    return entries


class ConsolidatedClient:
    """Consulta la legislación consolidada y su análisis normativo."""

    def __init__(self, http: BOEHttpClient) -> None:
        self._http = http

    async def get_meta(self, consolidated_id: str) -> ConsolidatedMeta | None:
        payload = await self._http.get_json(
            f"/legislacion-consolidada/id/{consolidated_id}/metadatos"
        )
        return parse_meta(payload) if payload else None

    async def get_index(self, consolidated_id: str) -> list[IndexBlock]:
        payload = await self._http.get_json(
            f"/legislacion-consolidada/id/{consolidated_id}/texto/indice"
        )
        return parse_index(payload) if payload else []

    async def get_references(self, consolidated_id: str) -> list[ReferenceEntry]:
        payload = await self._http.get_json(
            f"/legislacion-consolidada/id/{consolidated_id}/analisis"
        )
        return parse_references(payload) if payload else []
