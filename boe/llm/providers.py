"""Definición de proveedores LLM (todos OpenAI-compatible).

Groq y OpenRouter exponen la misma API que OpenAI, así que basta el SDK `openai`
apuntando a distintos `base_url`. Añadir un proveedor nuevo es una entrada aquí.
"""

from __future__ import annotations

from dataclasses import dataclass

from boe.core.config import settings


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str | None
    api_key: str | None
    model: str

    @property
    def available(self) -> bool:
        return bool(self.api_key)


def _providers() -> dict[str, Provider]:
    return {
        "groq": Provider(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        ),
        "openrouter": Provider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        ),
        "openai": Provider(
            name="openai",
            base_url=None,  # SDK usa el endpoint oficial por defecto
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        ),
    }


def get_provider(name: str) -> Provider | None:
    return _providers().get(name)


def resolve_chain() -> list[Provider]:
    """Orden de intento: primario y luego fallback, solo los disponibles."""
    chain: list[Provider] = []
    for name in (settings.llm_primary_provider, settings.llm_fallback_provider):
        if not name:
            continue
        provider = get_provider(name)
        if provider and provider.available and provider not in chain:
            chain.append(provider)
    return chain
