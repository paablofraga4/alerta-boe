"""Cliente HTTP async base para las APIs de datos abiertos del BOE.

Reemplaza las llamadas sueltas con `requests` repartidas por el código legacy.
Un único cliente con:
  - `Accept: application/json` por defecto,
  - reintentos con backoff exponencial (tenacity) ante errores de red/5xx,
  - `404 → None` (no hay BOE ese día / norma inexistente), sin excepción.
"""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from boe.core.config import settings


class BOEClientError(RuntimeError):
    """Error no recuperable al hablar con la API del BOE."""


_RETRYABLE = (httpx.TransportError, httpx.HTTPStatusError)


class BOEHttpClient:
    """Envoltura fina sobre httpx.AsyncClient con la política del BOE."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = (base_url or settings.boe_api_base).rstrip("/")
        self.timeout = timeout or settings.boe_request_timeout
        self.max_retries = max_retries or settings.boe_max_retries
        self._external_client = client
        self._client = client

    async def __aenter__(self) -> BOEHttpClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                follow_redirects=True,
            )
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._client is not None and self._external_client is None:
            await self._client.aclose()
            self._client = None

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise BOEClientError("Usa el cliente dentro de 'async with'.")
        return self._client

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict | None:
        """GET que devuelve el JSON, o None si el recurso no existe (404)."""
        client = self._require_client()
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"

        @retry(
            reraise=True,
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=16),
            retry=retry_if_exception_type(_RETRYABLE),
        )
        async def _do() -> dict | None:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()

        try:
            return await _do()
        except httpx.HTTPStatusError as exc:  # 4xx no recuperable tras reintentos
            raise BOEClientError(
                f"BOE respondió {exc.response.status_code} en {url}"
            ) from exc
        except httpx.HTTPError as exc:
            raise BOEClientError(f"Fallo de red al consultar {url}: {exc}") from exc


def as_list(value: Any) -> list[Any]:
    """Normaliza los campos del BOE que llegan como dict, lista, str o None.

    La API del BOE devuelve un objeto cuando hay un elemento y una lista cuando
    hay varios (y a veces una cadena). Esta función unifica ese caos —el mismo
    que hoy obliga a repetir `if isinstance(x, dict)` por todo `boe_fetcher.py`.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
