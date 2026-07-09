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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
