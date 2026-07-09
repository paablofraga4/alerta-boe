"""Comportamiento del cliente HTTP base: 404→None, reintentos, error final."""

import httpx
import pytest
import respx

from boe.clients.base import BOEClientError, BOEHttpClient

BASE = "https://boe.es/datosabiertos/api"


@respx.mock
async def test_404_returns_none():
    respx.get(f"{BASE}/boe/sumario/20240101").mock(return_value=httpx.Response(404))
    async with BOEHttpClient(base_url=BASE) as client:
        assert await client.get_json("/boe/sumario/20240101") is None


@respx.mock
async def test_retries_then_succeeds():
    route = respx.get(f"{BASE}/ping").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    async with BOEHttpClient(base_url=BASE, max_retries=3) as client:
        data = await client.get_json("/ping")
    assert data == {"ok": True}
    assert route.call_count == 2


@respx.mock
async def test_persistent_error_raises():
    respx.get(f"{BASE}/broken").mock(return_value=httpx.Response(500))
    async with BOEHttpClient(base_url=BASE, max_retries=2) as client:
        with pytest.raises(BOEClientError):
            await client.get_json("/broken")
