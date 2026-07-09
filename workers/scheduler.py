"""Worker de jobs programados (skeleton F0).

En F1 aquí se registran las etapas del pipeline (ingesta diaria del sumario,
extracción de texto, clasificación, resumen, embeddings, grafo). De momento
deja el andamiaje y un job de ejemplo, para tener el contenedor `worker` del
docker-compose arrancable desde el primer día.

Se usa APScheduler (no Celery): el volumen del BOE no justifica un broker.
"""

from __future__ import annotations

import asyncio
from datetime import date

import structlog

from boe.clients.base import BOEHttpClient
from boe.ingest.pipeline import Pipeline

log = structlog.get_logger(__name__)


async def daily_ingest(fecha: date | None = None) -> dict:
    """Ingesta y enriquece el BOE del día. Job diario del scheduler."""
    fecha = fecha or date.today()
    yyyymmdd = fecha.strftime("%Y%m%d")
    log.info("daily_ingest_start", fecha=yyyymmdd)
    async with BOEHttpClient() as http:
        counts = await Pipeline(http).run_full(yyyymmdd)
    log.info("daily_ingest_done", fecha=yyyymmdd, **counts)
    return counts


async def main() -> None:
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:  # pragma: no cover
        log.error("apscheduler_missing", hint="instala el extra [worker]")
        return

    scheduler = AsyncIOScheduler()
    # El BOE del día suele estar disponible a primera hora.
    scheduler.add_job(daily_ingest, CronTrigger(hour=8, minute=30))
    scheduler.start()
    log.info("worker_started")

    stop = asyncio.Event()
    await stop.wait()  # mantener vivo


if __name__ == "__main__":
    asyncio.run(main())
