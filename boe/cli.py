"""CLI de AlertaBOE.

Punto de entrada `boe` (definido en pyproject). En F0 ofrece diagnóstico y un
smoke test de los clientes del BOE; los comandos de ingesta completos llegan en F1.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime

from boe import __version__
from boe.clients import BOEHttpClient, SummaryClient
from boe.core.config import settings
from boe.llm.providers import resolve_chain


def _cmd_version(_: argparse.Namespace) -> None:
    print(f"AlertaBOE {__version__}")


def _cmd_check(_: argparse.Namespace) -> None:
    print("Configuración:")
    print(f"  BOE API base : {settings.boe_api_base}")
    print(f"  Base de datos: {settings.database_url.split('@')[-1]}")
    print(f"  Embeddings   : {settings.embeddings_model} (dim {settings.embeddings_dim})")
    chain = resolve_chain()
    if chain:
        print("  Proveedores LLM disponibles: " + ", ".join(p.name for p in chain))
    else:
        print("  Proveedores LLM disponibles: ninguno (define GROQ_API_KEY u otro)")


def _cmd_fetch_summary(args: argparse.Namespace) -> None:
    async def _run() -> None:
        async with BOEHttpClient() as http:
            items, raw = await SummaryClient(http).fetch(args.fecha)
        if raw is None:
            print(f"No hay BOE publicado para {args.fecha}")
            return
        print(f"{len(items)} publicaciones en el sumario del {args.fecha}:")
        for item in items[: args.limit]:
            print(f"  [{item.boe_id}] {item.title[:90]}")

    asyncio.run(_run())


def _cmd_ingest(args: argparse.Namespace) -> None:
    """Ingesta y enriquece un día completo (fetch → ... → grafo)."""
    from boe.ingest.pipeline import Pipeline

    async def _run() -> None:
        async with BOEHttpClient() as http:
            counts = await Pipeline(http).run_full(args.fecha, limit=args.limit)
        print(f"Ingesta del {args.fecha}: {json.dumps(counts, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_backfill(args: argparse.Namespace) -> None:
    """Ingesta un rango de fechas y enriquece lo pendiente."""
    from boe.ingest.pipeline import backfill, daterange_yyyymmdd

    desde = datetime.strptime(args.desde, "%Y-%m-%d").date()
    hasta = datetime.strptime(args.hasta, "%Y-%m-%d").date()
    fechas = daterange_yyyymmdd(desde, hasta)

    async def _run() -> None:
        async with BOEHttpClient() as http:
            counts = await backfill(http, fechas, limit=args.limit)
        print(f"Backfill {args.desde}..{args.hasta} ({len(fechas)} días): "
              f"{json.dumps(counts, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_enrich(args: argparse.Namespace) -> None:
    """Ejecuta las etapas de enriquecido sobre lo ya ingerido."""
    from boe.ingest.pipeline import Pipeline

    async def _run() -> None:
        async with BOEHttpClient() as http:
            counts = await Pipeline(http).run_all_enrich(limit=args.limit)
        print(f"Enriquecido: {json.dumps(counts, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_content_generate(args: argparse.Namespace) -> None:
    """Genera borradores de contenido para las mejores publicaciones de un día."""
    from datetime import datetime as _dt

    from boe.content.pipeline import ContentPipeline

    fecha = _dt.strptime(args.fecha, "%Y-%m-%d").date()

    async def _run() -> None:
        ids = await ContentPipeline().generate_for_date(fecha, top_n=args.top)
        print(f"Generados {len(ids)} borradores para {args.fecha}: {ids}")

    asyncio.run(_run())


def _cmd_content_list(args: argparse.Namespace) -> None:
    """Lista las piezas de contenido en cola."""
    from sqlalchemy import select

    from boe.core.db import SessionLocal
    from boe.core.models import ContentPost

    async def _run() -> None:
        async with SessionLocal() as session:
            stmt = select(ContentPost).order_by(ContentPost.id.desc()).limit(args.limit)
            posts = (await session.execute(stmt)).scalars().all()
        if not posts:
            print("No hay contenido en cola.")
            return
        for p in posts:
            print(f"  #{p.id} [{p.channel.value:8s}] {p.status.value:9s} "
                  f"score={p.interest_score} :: {(p.script or '')[:70]!r}")

    asyncio.run(_run())


def _cmd_digest_weekly(args: argparse.Namespace) -> None:
    """Envía el digest semanal «El BOE en 3 minutos» a las suscripciones activas."""
    from datetime import datetime as _dt

    from boe.alerts.digest import run_weekly

    hasta = _dt.strptime(args.hasta, "%Y-%m-%d").date() if args.hasta else None

    async def _run() -> None:
        result = await run_weekly(hasta)
        print(f"Digest semanal: {json.dumps(result, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_resummarize(args: argparse.Namespace) -> None:
    """Regenera al agente v2 (brief estructurado) los resúmenes antiguos."""
    from datetime import datetime as _dt

    from boe.enrich.resummarize import resummarize_pending

    since = _dt.strptime(args.since, "%Y-%m-%d").date() if args.since else None

    async def _run() -> None:
        result = await resummarize_pending(limit=args.limit, since=since)
        print(f"Re-resumen v2: {json.dumps(result, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_content_render(args: argparse.Namespace) -> None:
    """Renderiza los vídeos de las piezas TikTok aprobadas sin asset."""
    from pathlib import Path

    from boe.content.video.batch import render_approved

    async def _run() -> None:
        result = await render_approved(Path(args.out))
        print(f"Render de vídeos: {json.dumps(result, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_alerts_run(args: argparse.Namespace) -> None:
    """Casa los documentos de un día con las suscripciones y envía las alertas."""
    from datetime import datetime as _dt

    from boe.alerts.service import run_for_date

    fecha = _dt.strptime(args.fecha, "%Y-%m-%d").date()

    async def _run() -> None:
        result = await run_for_date(fecha)
        print(f"Alertas {args.fecha}: {json.dumps(result, ensure_ascii=False)}")

    asyncio.run(_run())


def _cmd_status(_: argparse.Namespace) -> None:
    """Muestra el estado del pipeline por etapa."""
    from boe.core.db import SessionLocal
    from boe.ingest.repository import stage_counts

    async def _run() -> None:
        async with SessionLocal() as session:
            summary = await stage_counts(session)
        if not summary:
            print("Pipeline vacío (aún no se ha ingerido nada).")
            return
        for stage, states in summary.items():
            detail = ", ".join(f"{k}={v}" for k, v in states.items())
            print(f"  {stage:16s} {detail}")

    asyncio.run(_run())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="boe", description="AlertaBOE CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("version", help="Muestra la versión").set_defaults(func=_cmd_version)
    sub.add_parser("check", help="Comprueba configuración y proveedores").set_defaults(
        func=_cmd_check
    )

    fs = sub.add_parser("fetch-summary", help="Descarga y parsea el sumario de una fecha")
    fs.add_argument("fecha", help="Fecha en formato AAAAMMDD")
    fs.add_argument("--limit", type=int, default=10)
    fs.set_defaults(func=_cmd_fetch_summary)

    ing = sub.add_parser("ingest", help="Ingesta y enriquece un día (AAAAMMDD)")
    ing.add_argument("fecha", help="Fecha en formato AAAAMMDD")
    ing.add_argument("--limit", type=int, default=500)
    ing.set_defaults(func=_cmd_ingest)

    bf = sub.add_parser("backfill", help="Ingesta un rango de fechas")
    bf.add_argument("desde", help="Fecha inicial AAAA-MM-DD")
    bf.add_argument("hasta", help="Fecha final AAAA-MM-DD")
    bf.add_argument("--limit", type=int, default=500)
    bf.set_defaults(func=_cmd_backfill)

    en = sub.add_parser("enrich", help="Ejecuta el enriquecido sobre lo ingerido")
    en.add_argument("--limit", type=int, default=500)
    en.set_defaults(func=_cmd_enrich)

    sub.add_parser("status", help="Estado del pipeline por etapa").set_defaults(
        func=_cmd_status
    )

    cg = sub.add_parser("content-generate", help="Genera borradores de contenido de un día")
    cg.add_argument("fecha", help="Fecha AAAA-MM-DD")
    cg.add_argument("--top", type=int, default=3, help="Nº de publicaciones a cubrir")
    cg.set_defaults(func=_cmd_content_generate)

    cl = sub.add_parser("content-list", help="Lista el contenido en cola")
    cl.add_argument("--limit", type=int, default=20)
    cl.set_defaults(func=_cmd_content_list)

    ar = sub.add_parser("alerts-run", help="Envía las alertas casadas de un día")
    ar.add_argument("fecha", help="Fecha AAAA-MM-DD")
    ar.set_defaults(func=_cmd_alerts_run)

    dw = sub.add_parser("digest-weekly", help="Envía el digest semanal a las suscripciones")
    dw.add_argument("--hasta", help="Último día de la semana AAAA-MM-DD (defecto: hoy)")
    dw.set_defaults(func=_cmd_digest_weekly)

    rs = sub.add_parser("resummarize", help="Regenera resúmenes antiguos al agente v2")
    rs.add_argument("--limit", type=int, default=100, help="Máximo de resúmenes a regenerar")
    rs.add_argument("--since", help="Solo desde esta fecha AAAA-MM-DD (opcional)")
    rs.set_defaults(func=_cmd_resummarize)

    cr = sub.add_parser("content-render", help="Renderiza los vídeos aprobados sin asset")
    cr.add_argument("--out", default="data/videos", help="Directorio de salida de los mp4")
    cr.set_defaults(func=_cmd_content_render)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
