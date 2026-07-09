"""Migración one-shot del esquema legacy al esquema nuevo (F0).

Lee las tablas del AlertaBOE antiguo (`publications`, `regions`, `scopes`,
`legislaciones`) vía SQL crudo —para no acoplar el código nuevo a los modelos
viejos— y las vuelca en el esquema 2.0. Idempotente por `boe_id`.

Uso:
    python -m boe.ingest.migrate_legacy \
        --legacy postgresql+psycopg://user:pass@host:5432/alertaBOE_viejo

Si no se pasa `--legacy`, no hace nada (evita ejecuciones accidentales).
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession

from boe.core.db import SessionLocal
from boe.core.enums import PipelineStage, Scope, StageStatus
from boe.core.models import Document, PipelineState, Summary

_SCOPE_MAP = {
    "Europeo": Scope.EUROPEO,
    "Nacional": Scope.NACIONAL,
    "Autonómico": Scope.AUTONOMICO,
}


def _read_legacy_publications(legacy_url: str) -> list[dict]:
    engine = create_engine(legacy_url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT p.boe_id, p.date, p.title, p.departamento, p.seccion,
                           p.epigrafe, p.url_html, p.url_pdf, p.pages,
                           p.resumen, p.resumen_tiktok, s.name AS scope_name
                    FROM publications p
                    LEFT JOIN scopes s ON s.id = p.scope_id
                    WHERE p.boe_id IS NOT NULL
                    """
                )
            ).mappings()
            return [dict(r) for r in rows]
    finally:
        engine.dispose()


async def _upsert(session: AsyncSession, rows: list[dict]) -> int:
    migrated = 0
    for row in rows:
        existing = await session.execute(
            text("SELECT id FROM documents WHERE boe_id = :bid"),
            {"bid": row["boe_id"]},
        )
        if existing.first():
            continue

        doc = Document(
            boe_id=row["boe_id"],
            published_at=row["date"],
            title=row["title"] or "[Sin título]",
            departamento=row.get("departamento"),
            seccion=row.get("seccion"),
            epigrafe=row.get("epigrafe"),
            url_html=row.get("url_html"),
            url_pdf=row.get("url_pdf"),
            pages=row.get("pages"),
            scope=_SCOPE_MAP.get(row.get("scope_name"), Scope.OTRO),
        )
        session.add(doc)
        await session.flush()

        if row.get("resumen") or row.get("resumen_tiktok"):
            session.add(
                Summary(
                    document_id=doc.id,
                    long=row.get("resumen"),
                    short=row.get("resumen_tiktok"),
                    model="legacy",
                    prompt_version="legacy",
                )
            )
            session.add(
                PipelineState(
                    document_id=doc.id,
                    stage=PipelineStage.SUMMARIZED,
                    status=StageStatus.DONE,
                )
            )
        migrated += 1

    await session.commit()
    return migrated


async def run(legacy_url: str) -> None:
    rows = _read_legacy_publications(legacy_url)
    print(f"Leídas {len(rows)} publicaciones del esquema legacy.")
    async with SessionLocal() as session:
        migrated = await _upsert(session, rows)
    print(f"Migradas {migrated} publicaciones nuevas al esquema 2.0.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra el AlertaBOE legacy al esquema 2.0")
    parser.add_argument("--legacy", required=True, help="URL SQLAlchemy de la DB antigua")
    args = parser.parse_args()
    asyncio.run(run(args.legacy))


if __name__ == "__main__":
    main()
