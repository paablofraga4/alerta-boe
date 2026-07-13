"""Test de integración del pipeline completo contra Postgres+pgvector real.

Mockea toda la red del BOE con respx (sumario, HTML y análisis) y ejerce las
etapas reales fetch → text → classify → summarize → embed → link, comprobando
el estado del pipeline y que el grafo normativo se construye.

Se salta automáticamente si no hay Postgres (fixture `session_factory`).
"""

import httpx
import respx
from sqlalchemy import func, select

from boe.clients.base import BOEHttpClient
from boe.core.enums import PipelineStage, ReferenceType, StageStatus
from boe.core.models import Document, PipelineState, Reference
from boe.ingest.pipeline import Pipeline

BASE = "https://boe.es/datosabiertos/api"

_HTML = """<html><body><div class="documento">
<h1>Ayudas a autónomos</h1><p>El Gobierno aprueba ayudas para autónomos en Galicia.</p>
</div></body></html>"""


def _mock_boe(sumario, analisis):
    respx.get(f"{BASE}/boe/sumario/20240709").mock(
        return_value=httpx.Response(200, json=sumario)
    )
    # HTML de cada publicación (cualquier txt.php).
    respx.get(url__regex=r"https://boe\.es/diario_boe/txt\.php.*").mock(
        return_value=httpx.Response(200, text=_HTML)
    )
    # Análisis solo del documento consolidable (sección 1).
    respx.get(f"{BASE}/legislacion-consolidada/id/BOE-A-2024-0001/analisis").mock(
        return_value=httpx.Response(200, json=analisis)
    )


@respx.mock
async def test_full_pipeline_builds_graph(session_factory, sumario, analisis):
    _mock_boe(sumario, analisis)

    async with BOEHttpClient(base_url=BASE) as http:
        pipeline = Pipeline(http, session_factory=session_factory)
        counts = await pipeline.run_full("20240709")

    # Ingesta: 3 publicaciones válidas del sumario.
    assert counts["fetched"] == 3
    assert counts["text"] == 3
    assert counts["classified"] == 3
    # Sin proveedor LLM en test → resumen se salta (no falla).
    assert counts["summarized"] == 3
    # Solo la sección 1 es consolidable → 1 documento enlazado.
    assert counts["linked"] == 1

    async with session_factory() as session:
        # El documento consolidable tiene sus referencias (grafo).
        doc = (
            await session.execute(
                select(Document).where(Document.boe_id == "BOE-A-2024-0001")
            )
        ).scalar_one()
        assert doc.consolidated_id == "BOE-A-2024-0001"
        assert doc.full_text and "autónomos" in doc.full_text.lower()

        refs = (
            await session.execute(select(Reference).where(Reference.source_id == doc.id))
        ).scalars().all()
        assert len(refs) == 3  # 2 anteriores + 1 posterior
        assert any(r.rel_type == ReferenceType.MODIFICA for r in refs)

        # El resumen quedó SKIPPED (no DONE) por no haber LLM.
        summ_state = (
            await session.execute(
                select(PipelineState.status).where(
                    PipelineState.document_id == doc.id,
                    PipelineState.stage == PipelineStage.SUMMARIZED,
                )
            )
        ).scalar_one()
        assert summ_state == StageStatus.SKIPPED


@respx.mock
async def test_pipeline_is_idempotent(session_factory, sumario, analisis):
    _mock_boe(sumario, analisis)

    async with BOEHttpClient(base_url=BASE) as http:
        pipeline = Pipeline(http, session_factory=session_factory)
        await pipeline.run_full("20240709")
        # Segunda pasada: no debe crear documentos ni referencias nuevas.
        second = await pipeline.run_full("20240709")

    assert second["fetched"] == 0
    assert second["text"] == 0  # ya estaban DONE
    assert second["linked"] == 0

    async with session_factory() as session:
        n_docs = (await session.execute(select(func.count(Document.id)))).scalar_one()
        n_refs = (await session.execute(select(func.count(Reference.id)))).scalar_one()
    assert n_docs == 3
    assert n_refs == 3
