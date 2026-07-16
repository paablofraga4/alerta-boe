"""El backfill regenera solo los resúmenes que no son v2, in situ e idempotente."""

from datetime import date

from sqlalchemy import select

from boe.core.enums import Scope
from boe.core.models import Document, Summary
from boe.enrich.resummarize import resummarize_pending
from boe.llm.prompts import DocumentBrief


class _FakeRouter:
    has_provider = True

    async def complete(self, *a, **k):  # map (no se usa con texto corto)
        return "hechos"

    async def complete_structured(self, messages, schema, **k):
        return schema(
            long="Nuevo resumen v2.",
            short="Alerta v2.",
            hook="Gancho v2.",
            que_regula="Regula algo.",
            a_quien_afecta=["autónomos"],
            puntos_clave=["p1", "p2"],
            plazos=[{"fecha": "30 de septiembre de 2026", "accion": "solicitar"}],
            que_hacer=["haz esto"],
        )


async def _seed(session_factory):
    async with session_factory() as s:
        d1 = Document(
            boe_id="BOE-A-2024-0001",
            published_at=date(2024, 7, 9),
            title="Ayudas a autónomos",
            full_text="El Gobierno aprueba ayudas para autónomos.",
            scope=Scope.NACIONAL,
        )
        d2 = Document(
            boe_id="BOE-A-2024-0002",
            published_at=date(2024, 7, 9),
            title="Otra norma",
            full_text="Texto.",
            scope=Scope.OTRO,
        )
        s.add_all([d1, d2])
        await s.flush()
        # d1: resumen viejo v1 (sin structured) → debe regenerarse.
        s.add(Summary(document_id=d1.id, short="viejo", model="x", prompt_version="v1"))
        # d2: ya v2 con structured → NO debe tocarse.
        s.add(
            Summary(
                document_id=d2.id,
                long="ya v2",
                short="ya",
                hook="ya",
                structured={"plazos": []},
                model="llm",
                prompt_version="v2",
            )
        )
        await s.commit()


async def test_resummarize_only_touches_v1(session_factory):
    await _seed(session_factory)
    result = await resummarize_pending(
        router=_FakeRouter(), session_factory=session_factory
    )
    assert result["actualizados"] == 1
    assert result["fallidos"] == 0

    async with session_factory() as s:
        summaries = {
            row.document_id: row
            for row in (await s.execute(select(Summary))).scalars().all()
        }
        docs = {
            row.id: row.boe_id
            for row in (await s.execute(select(Document))).scalars().all()
        }
    by_boe = {docs[did]: sm for did, sm in summaries.items()}
    # d1 quedó regenerado a v2 con structured poblado.
    assert by_boe["BOE-A-2024-0001"].prompt_version == "v2"
    assert by_boe["BOE-A-2024-0001"].structured["plazos"][0]["accion"] == "solicitar"
    # d2 intacto.
    assert by_boe["BOE-A-2024-0002"].long == "ya v2"


async def test_resummarize_is_idempotent(session_factory):
    await _seed(session_factory)
    await resummarize_pending(router=_FakeRouter(), session_factory=session_factory)
    # Segunda pasada: nada pendiente.
    second = await resummarize_pending(
        router=_FakeRouter(), session_factory=session_factory
    )
    assert second["actualizados"] == 0
    assert second["pendientes"] == 0


def test_brief_dump_shape():
    b = DocumentBrief(long="l", short="s", hook="h", plazos=[])
    dumped = b.model_dump(exclude={"long", "short", "hook"})
    assert set(dumped) == {"que_regula", "a_quien_afecta", "puntos_clave", "plazos", "que_hacer"}
