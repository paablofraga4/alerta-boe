import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def sumario() -> dict:
    return load_fixture("sumario.json")


@pytest.fixture
def analisis() -> dict:
    return load_fixture("analisis.json")


@pytest.fixture
def metadatos() -> dict:
    return load_fixture("metadatos.json")
