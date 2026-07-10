"""Dependencias comunes de la API."""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from boe.core.config import settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Valida la API key.

    Si no hay claves configuradas (`API_KEYS` vacío), la API queda abierta —
    cómodo en desarrollo. En cuanto se define al menos una, se exige la cabecera
    `X-API-Key`. Habilita desde el día 1 la "API pública para desarrolladores".
    """
    keys = settings.api_keys_set
    if not keys:
        return
    if x_api_key not in keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o ausente (cabecera X-API-Key).",
        )
