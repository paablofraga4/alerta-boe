"""Router LLM con fallback entre proveedores y salidas estructuradas.

Una sola interfaz para todo el producto. El código de negocio pide un resumen o
una clasificación sin saber si detrás está Groq u OpenRouter; el router prueba
el proveedor primario y cae al fallback si falla. Sin LangChain: SDK `openai`
directo + validación Pydantic.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel

from boe.llm.providers import Provider, resolve_chain

log = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

Message = dict[str, str]


class LLMError(RuntimeError):
    """Todos los proveedores de la cadena fallaron."""


class LLMRouter:
    def __init__(self, chain: list[Provider] | None = None) -> None:
        self._chain = chain if chain is not None else resolve_chain()
        self._clients: dict[str, AsyncOpenAI] = {}

    @property
    def has_provider(self) -> bool:
        return bool(self._chain)

    def _client(self, provider: Provider) -> AsyncOpenAI:
        if provider.name not in self._clients:
            self._clients[provider.name] = AsyncOpenAI(
                api_key=provider.api_key,
                base_url=provider.base_url,
            )
        return self._clients[provider.name]

    async def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.4,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """Devuelve el texto de la respuesta, probando la cadena de proveedores."""
        if not self._chain:
            raise LLMError(
                "No hay proveedor LLM configurado (define GROQ_API_KEY u otro)."
            )

        last_error: Exception | None = None
        for provider in self._chain:
            try:
                kwargs: dict = {
                    "model": provider.model,
                    "messages": messages,
                    "temperature": temperature,
                }
                if max_tokens:
                    kwargs["max_tokens"] = max_tokens
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                resp = await self._client(provider).chat.completions.create(**kwargs)
                return (resp.choices[0].message.content or "").strip()
            except Exception as exc:  # noqa: BLE001 — se registra y se prueba el siguiente
                last_error = exc
                log.warning("llm_provider_failed", provider=provider.name, error=str(exc))
                continue

        raise LLMError(f"Todos los proveedores LLM fallaron: {last_error}")

    async def complete_structured(
        self,
        messages: list[Message],
        schema: type[T],
        *,
        temperature: float = 0.2,
    ) -> T:
        """Pide JSON y lo valida contra un modelo Pydantic."""
        raw = await self.complete(messages, temperature=temperature, json_mode=True)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError(f"El modelo no devolvió JSON válido: {raw[:200]}") from exc
        return schema.model_validate(data)


@lru_cache
def get_router() -> LLMRouter:
    return LLMRouter()
