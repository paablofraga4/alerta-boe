"""El router LLM debe caer al fallback y validar salida estructurada.

No se llama a ninguna API real: se inyecta una cadena de proveedores falsos y
se parchea la creación de clientes.
"""

import pytest

from boe.llm.prompts import SummaryOutput
from boe.llm.providers import Provider
from boe.llm.router import LLMError, LLMRouter


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, behavior):
        self._behavior = behavior

    async def create(self, **kwargs):
        result = self._behavior(kwargs)
        if isinstance(result, Exception):
            raise result
        return _FakeResponse(result)


class _FakeClient:
    def __init__(self, behavior):
        self.chat = type("Chat", (), {"completions": _FakeCompletions(behavior)})()


def _provider(name, model):
    return Provider(name=name, base_url=None, api_key="x", model=model)


async def test_falls_back_to_second_provider(monkeypatch):
    primary = _provider("groq", "m1")
    fallback = _provider("openrouter", "m2")
    router = LLMRouter(chain=[primary, fallback])

    def make_client(provider):
        if provider.name == "groq":
            return _FakeClient(lambda k: RuntimeError("rate limit"))
        return _FakeClient(lambda k: "respuesta del fallback")

    monkeypatch.setattr(router, "_client", make_client)
    out = await router.complete([{"role": "user", "content": "hola"}])
    assert out == "respuesta del fallback"


async def test_raises_when_all_fail(monkeypatch):
    router = LLMRouter(chain=[_provider("groq", "m1")])
    monkeypatch.setattr(
        router, "_client", lambda p: _FakeClient(lambda k: RuntimeError("boom"))
    )
    with pytest.raises(LLMError):
        await router.complete([{"role": "user", "content": "x"}])


async def test_no_provider_configured():
    router = LLMRouter(chain=[])
    assert router.has_provider is False
    with pytest.raises(LLMError):
        await router.complete([{"role": "user", "content": "x"}])


async def test_structured_output_validates(monkeypatch):
    router = LLMRouter(chain=[_provider("groq", "m1")])
    payload = '{"long": "resumen largo", "short": "alerta", "hook": "gancho"}'
    monkeypatch.setattr(router, "_client", lambda p: _FakeClient(lambda k: payload))
    out = await router.complete_structured(
        [{"role": "user", "content": "x"}], SummaryOutput
    )
    assert isinstance(out, SummaryOutput)
    assert out.short == "alerta"
