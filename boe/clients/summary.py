"""Cliente del sumario diario del BOE.

`GET /boe/sumario/{AAAAMMDD}` → todas las publicaciones del día.

La estructura del BOE anida seccion → departamento → (epigrafe →) item, y cada
nivel puede venir como objeto o como lista. `parse_summary` aplana todo eso a
una lista limpia de `SummaryItem`, con parsing tolerante a fallos.
"""

from __future__ import annotations

from boe.clients.base import BOEHttpClient, as_list
from boe.clients.dto import SummaryItem


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _pages(url_pdf: dict) -> int | None:
    ini = _int_or_none(url_pdf.get("pagina_inicial"))
    fin = _int_or_none(url_pdf.get("pagina_final"))
    if ini is None or fin is None:
        return None
    return fin - ini + 1


def _parse_item(
    item: dict,
    seccion: str | None,
    seccion_codigo: str | None,
    departamento: str | None,
    epigrafe: str | None,
) -> SummaryItem | None:
    boe_id = item.get("identificador")
    if not boe_id:
        return None

    url_pdf_raw = item.get("url_pdf")
    url_pdf = url_pdf_raw if isinstance(url_pdf_raw, dict) else {}

    return SummaryItem(
        boe_id=boe_id,
        title=item.get("titulo") or "[Sin título]",
        seccion=seccion,
        seccion_codigo=seccion_codigo,
        departamento=departamento,
        epigrafe=epigrafe,
        url_html=item.get("url_html"),
        url_pdf=url_pdf.get("texto") if url_pdf else item.get("url_pdf"),
        url_xml=item.get("url_xml"),
        pages=_pages(url_pdf) if url_pdf else None,
    )


def parse_summary(payload: dict) -> list[SummaryItem]:
    """Aplana el JSON del sumario a una lista de publicaciones."""
    items: list[SummaryItem] = []
    try:
        diario = payload["data"]["sumario"]["diario"]
    except (KeyError, TypeError):
        return items

    for dia in as_list(diario):
        for seccion in as_list(dia.get("seccion")):
            sec_nombre = seccion.get("nombre")
            sec_codigo = seccion.get("codigo")

            for departamento in as_list(seccion.get("departamento")):
                if isinstance(departamento, str):
                    departamento = {"nombre": departamento}
                dep_nombre = departamento.get("nombre")

                # Caso 1: departamento → epigrafe → item
                epigrafes = as_list(departamento.get("epigrafe"))
                if epigrafes:
                    for epigrafe in epigrafes:
                        epi_nombre = epigrafe.get("nombre")
                        for item in as_list(epigrafe.get("item")):
                            parsed = _parse_item(
                                item, sec_nombre, sec_codigo, dep_nombre, epi_nombre
                            )
                            if parsed:
                                items.append(parsed)
                # Caso 2: departamento → item (sin epígrafe)
                else:
                    for item in as_list(departamento.get("item")):
                        parsed = _parse_item(
                            item, sec_nombre, sec_codigo, dep_nombre, None
                        )
                        if parsed:
                            items.append(parsed)

    return items


class SummaryClient:
    """Consulta y parsea el sumario diario."""

    def __init__(self, http: BOEHttpClient) -> None:
        self._http = http

    async def fetch(self, fecha_yyyymmdd: str) -> tuple[list[SummaryItem], dict | None]:
        """Devuelve (items, raw_json). Lista vacía y None si no hay BOE ese día."""
        payload = await self._http.get_json(f"/boe/sumario/{fecha_yyyymmdd}")
        if payload is None:
            return [], None
        return parse_summary(payload), payload
