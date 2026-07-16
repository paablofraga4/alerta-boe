"""El agente por documento lee el texto completo (map-reduce) y produce un brief.

No se llama a ningún LLM real: se inyecta un router falso que registra cuántas
veces se hace 'map' (complete) y devuelve un brief estructurado en el 'reduce'.
"""

from boe.enrich.document_agent import (
    SINGLE_PASS_CHARS,
    chunk_text,
    summarize_document,
)
from boe.llm.prompts import DocumentBrief


class _FakeRouter:
    """Cuenta llamadas de map y sirve un brief fijo en el reduce."""

    def __init__(self) -> None:
        self.map_calls = 0
        self.reduce_calls = 0
        self.last_reduce_text = ""

    async def complete(self, messages, *, temperature=0.4, **_):
        self.map_calls += 1
        # Devuelve un "hecho" derivado del fragmento para poder rastrearlo.
        return f"hechos-{self.map_calls}"

    async def complete_structured(self, messages, schema, *, temperature=0.2):
        self.reduce_calls += 1
        # El texto del reduce viaja en el último mensaje (user).
        self.last_reduce_text = messages[-1]["content"]
        return schema(
            long="Resumen largo.\n\nSegundo párrafo.",
            short="Alerta breve.",
            hook="Gancho.",
            que_regula="Regula X.",
            a_quien_afecta=["autónomos"],
            puntos_clave=["punto 1", "punto 2"],
            plazos=[{"fecha": "30 de junio", "accion": "solicitar"}],
            que_hacer=["pedir la ayuda"],
        )


def test_chunk_text_short_returns_single():
    assert chunk_text("hola mundo") == ["hola mundo"]


def test_chunk_text_long_overlaps_and_covers():
    texto = "\n".join(f"linea {i}" for i in range(2000))
    chunks = chunk_text(texto, size=1000, overlap=100)
    assert len(chunks) > 1
    # Ningún fragmento excede el tamaño pedido (con margen del solape/corte).
    assert all(len(c) <= 1000 for c in chunks)


async def test_short_document_single_pass():
    router = _FakeRouter()
    brief, version = await summarize_document(router, "Texto corto del BOE.", "Título")
    assert isinstance(brief, DocumentBrief)
    assert router.map_calls == 0  # texto corto → sin map-reduce
    assert router.reduce_calls == 1
    assert version == "v2"
    assert brief.puntos_clave == ["punto 1", "punto 2"]


async def test_long_document_uses_map_reduce():
    router = _FakeRouter()
    texto = "x" * (SINGLE_PASS_CHARS + 6000)
    brief, _ = await summarize_document(router, texto, "Título largo")
    assert router.map_calls >= 2  # se troceó y se leyó por partes
    assert router.reduce_calls == 1
    # El reduce recibe los hechos extraídos, no el texto bruto entero.
    assert "hechos-1" in router.last_reduce_text
    assert isinstance(brief, DocumentBrief)


async def test_empty_document_summarizes_title():
    router = _FakeRouter()
    brief, _ = await summarize_document(router, "", "Solo el titular")
    assert router.map_calls == 0
    assert router.reduce_calls == 1
    assert brief.short == "Alerta breve."
