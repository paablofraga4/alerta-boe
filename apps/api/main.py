"""Punto de entrada de la API pública (`/v1`).

Sustituye al antiguo `app/main.py`. Async de principio a fin, versionada, con
la capa HTTP separada del dominio (que vive en el paquete `boe`).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from boe import __version__
from boe.core.config import settings

from .routers import documents, health

app = FastAPI(
    title="AlertaBOE API",
    description="Democratiza el BOE: publicaciones, hilo normativo y búsqueda.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(documents.router, prefix="/v1", tags=["documents"])
