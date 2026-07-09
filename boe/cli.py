"""CLI de AlertaBOE.

Punto de entrada `boe` (definido en pyproject). En F0 ofrece diagnóstico y un
smoke test de los clientes del BOE; los comandos de ingesta completos llegan en F1.
"""

from __future__ import annotations

import argparse
import asyncio

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

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
