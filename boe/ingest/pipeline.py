"""Runner del pipeline de ingesta/enriquecido por etapas.

Cada etapa es idempotente y reanudable: su progreso vive en `pipeline_state`,
así que el pipeline se puede parar y retomar sin duplicar trabajo. El orden es:

    FETCHED → TEXT_EXTRACTED → CLASSIFIED → SUMMARIZED → EMBEDDED
                     └────────────────────────────────→ LINKED (solo consolidables)

Las etapas que necesitan recursos opcionales (LLM, modelo de embeddings) se
marcan SKIPPED si no están configurados, en vez de fallar.
"""

from __future__ import annotations

from datetime import date, datetime

import structlog
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from boe.clients.base import BOEHttpClient
from boe.clients.consolidated import ConsolidatedClient
from boe.clients.summary import SummaryClient
from boe.core.db import SessionLocal
from boe.core.enums import PipelineStage, StageStatus
from boe.core.models import Document, Embedding, Summary
from boe.enrich.classify import classify_by_regex
from boe.enrich.regions import detect_regions, detect_scope
from boe.enrich.summarize import summarize
from boe.enrich.text import fetch_text
from boe.graph.builder import store_references
from boe.ingest import repository as repo
from boe.llm.router import LLMRouter, get_router

log = structlog.get_logger(__name__)

# Etapa → predecesora que debe estar DONE para poder ejecutarla.
PREDECESSOR: dict[PipelineStage, PipelineStage | None] = {
    PipelineStage.TEXT_EXTRACTED: PipelineStage.FETCHED,
    PipelineStage.CLASSIFIED: PipelineStage.TEXT_EXTRACTED,
    PipelineStage.SUMMARIZED: PipelineStage.CLASSIFIED,
    PipelineStage.EMBEDDED: PipelineStage.SUMMARIZED,
    PipelineStage.LINKED: PipelineStage.FETCHED,
}

# Orden en el que se ejecutan las etapas de enriquecido en un `run_all`.
ENRICH_STAGES = [
    PipelineStage.TEXT_EXTRACTED,
    PipelineStage.CLASSIFIED,
    PipelineStage.SUMMARIZED,
    PipelineStage.EMBEDDED,
    PipelineStage.LINKED,
]


class Pipeline:
    def __init__(
        self,
        http: BOEHttpClient,
        *,
        session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
        router: LLMRouter | None = None,
        max_attempts: int = 3,
    ) -> None:
        self._http = http
        self._session_factory = session_factory
        self._router = router if router is not None else get_router()
        self._max_attempts = max_attempts
        self._summary = SummaryClient(http)
        self._consolidated = ConsolidatedClient(http)

    # ── Ingesta del sumario (etapa FETCHED) ──────────────────────────────────

    async def ingest_date(self, fecha_yyyymmdd: str) -> int:
        """Descarga el sumario del día y crea/actualiza documentos. Devuelve nº nuevos."""
        items, raw = await self._summary.fetch(fecha_yyyymmdd)
        if raw is None:
            log.info("no_boe_for_date", fecha=fecha_yyyymmdd)
            return 0

        published = datetime.strptime(fecha_yyyymmdd, "%Y%m%d").date()
        created = 0
        async with self._session_factory() as session:
            for item in items:
                doc, is_new = await repo.upsert_document(session, item, published)
                if is_new:
                    created += 1
                await repo.set_stage(
                    session, doc.id, PipelineStage.FETCHED, StageStatus.DONE
                )
            await session.commit()
        log.info("ingest_date_done", fecha=fecha_yyyymmdd, nuevos=created, total=len(items))
        return created

    # ── Etapas de enriquecido ────────────────────────────────────────────────

    async def run_stage(self, stage: PipelineStage, *, limit: int = 100) -> int:
        """Procesa hasta `limit` documentos listos para `stage`. Devuelve nº procesados."""
        async with self._session_factory() as session:
            docs = await repo.documents_ready_for(
                session,
                stage,
                PREDECESSOR.get(stage),
                limit=limit,
                max_attempts=self._max_attempts,
                require_consolidated=(stage == PipelineStage.LINKED),
            )

        processed = 0
        for doc_ref in docs:
            await self._process_one(doc_ref.id, stage)
            processed += 1
        if processed:
            log.info("stage_done", stage=stage.value, procesados=processed)
        return processed

    async def _process_one(self, document_id: int, stage: PipelineStage) -> None:
        """Procesa un documento en una etapa, en su propia transacción."""
        async with self._session_factory() as session:
            doc = await session.get(Document, document_id)
            if doc is None:
                return
            try:
                status = await self._handle(session, doc, stage)
                await repo.set_stage(session, doc.id, stage, status)
                await session.commit()
            except Exception as exc:  # noqa: BLE001 — se registra y se marca FAILED
                await session.rollback()
                async with self._session_factory() as err_session:
                    await repo.set_stage(
                        err_session,
                        document_id,
                        stage,
                        StageStatus.FAILED,
                        error=str(exc)[:500],
                        bump_attempt=True,
                    )
                    await err_session.commit()
                log.warning("stage_failed", stage=stage.value, doc=document_id, error=str(exc))

    async def _handle(
        self, session: AsyncSession, doc: Document, stage: PipelineStage
    ) -> StageStatus:
        if stage == PipelineStage.TEXT_EXTRACTED:
            doc.full_text = await fetch_text(self._http, doc.url_html)
            return StageStatus.DONE

        if stage == PipelineStage.CLASSIFIED:
            # Carga las colecciones N:M antes de mutarlas (evita lazy-load en async).
            await session.refresh(doc, attribute_names=["regions", "topics"])
            base = doc.full_text or " ".join(
                filter(None, [doc.seccion, doc.departamento, doc.epigrafe, doc.title])
            )
            doc.scope = detect_scope(base)
            await repo.attach_regions(session, doc, detect_regions(base))
            await repo.attach_topics(session, doc, classify_by_regex(base))
            return StageStatus.DONE

        if stage == PipelineStage.SUMMARIZED:
            if not self._router.has_provider:
                return StageStatus.SKIPPED
            result, version = await summarize(self._router, doc.full_text or "", doc.title)
            session.add(
                Summary(
                    document_id=doc.id,
                    long=result.long,
                    short=result.short,
                    hook=result.hook,
                    model="llm",
                    prompt_version=version,
                )
            )
            return StageStatus.DONE

        if stage == PipelineStage.EMBEDDED:
            try:
                from boe.search.embeddings import embed_document_text
            except ImportError:
                return StageStatus.SKIPPED
            vector = embed_document_text(doc.title, doc.full_text)
            await session.execute(
                insert(Embedding)
                .values(document_id=doc.id, model="local", vector=vector)
                .on_conflict_do_update(
                    index_elements=[Embedding.document_id],
                    set_={"vector": vector, "model": "local"},
                )
            )
            return StageStatus.DONE

        if stage == PipelineStage.LINKED:
            if not doc.consolidated_id:
                return StageStatus.SKIPPED
            entries = await self._consolidated.get_references(doc.consolidated_id)
            await store_references(session, doc.id, entries)
            return StageStatus.DONE

        raise ValueError(f"Etapa desconocida: {stage}")

    # ── Flujos de alto nivel ─────────────────────────────────────────────────

    async def run_all_enrich(self, *, limit: int = 500) -> dict[str, int]:
        """Ejecuta todas las etapas de enriquecido una vez, en orden."""
        counts: dict[str, int] = {}
        for stage in ENRICH_STAGES:
            counts[stage.value] = await self.run_stage(stage, limit=limit)
        return counts

    async def run_full(self, fecha_yyyymmdd: str, *, limit: int = 500) -> dict[str, int]:
        """Ingesta un día y lo enriquece de principio a fin."""
        created = await self.ingest_date(fecha_yyyymmdd)
        counts = await self.run_all_enrich(limit=limit)
        return {"fetched": created, **counts}


async def backfill(
    http: BOEHttpClient, fechas: list[str], *, limit: int = 500
) -> dict[str, int]:
    """Ingesta un rango de fechas y enriquece todo lo pendiente al final."""
    pipeline = Pipeline(http)
    total_new = 0
    for fecha in fechas:
        total_new += await pipeline.ingest_date(fecha)
    counts = await pipeline.run_all_enrich(limit=limit)
    return {"fetched": total_new, **counts}


def daterange_yyyymmdd(desde: date, hasta: date) -> list[str]:
    """Lista de fechas AAAAMMDD entre dos fechas (inclusive)."""
    days = (hasta - desde).days
    return [
        (date.fromordinal(desde.toordinal() + i)).strftime("%Y%m%d")
        for i in range(days + 1)
    ]
