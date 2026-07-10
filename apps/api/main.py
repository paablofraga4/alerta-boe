"""Punto de entrada de la API pública (`/v1`).

Sustituye al antiguo `app/main.py`. Async de principio a fin, versionada, con
la capa HTTP separada del dominio (que vive en el paquete `boe`).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from boe import __version__
from boe.core.config import settings

from .deps import require_api_key
from .routers import chat, digest, documents, health, search

app = FastAPI(
    title="AlertaBOE API",
    description="Democratiza el BOE: publicaciones, hilo normativo, búsqueda y chat.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Salud sin auth; el resto de /v1 protegido por API key (abierta si no hay claves).
app.include_router(health.router, tags=["health"])
_v1 = [Depends(require_api_key)]
app.include_router(documents.router, prefix="/v1", tags=["documents"], dependencies=_v1)
app.include_router(digest.router, prefix="/v1", tags=["digest"], dependencies=_v1)
app.include_router(search.router, prefix="/v1", tags=["search"], dependencies=_v1)
app.include_router(chat.router, prefix="/v1", tags=["chat"], dependencies=_v1)
