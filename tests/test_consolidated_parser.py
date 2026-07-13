"""Parsing de metadatos y del bloque `analisis` (aristas del grafo normativo)."""

from boe.clients.consolidated import parse_meta, parse_references
from boe.core.enums import ReferenceDirection, ReferenceType


def test_parse_meta(metadatos):
    meta = parse_meta(metadatos)
    assert meta is not None
    assert meta.consolidated_id == "BOE-A-2020-1000"
    assert meta.rango == "Ley"
    assert meta.departamento == "Jefatura del Estado"
    assert meta.vigente is True


def test_parse_references_directions_and_types(analisis):
    refs = parse_references(analisis)
    # 2 anteriores (lista) + 1 posterior (objeto suelto) = 3.
    assert len(refs) == 3

    anteriores = [r for r in refs if r.direction == ReferenceDirection.ANTERIOR]
    posteriores = [r for r in refs if r.direction == ReferenceDirection.POSTERIOR]
    assert len(anteriores) == 2
    assert len(posteriores) == 1

    modifica = next(r for r in refs if r.target_boe_id == "BOE-A-2020-1000")
    assert modifica.rel_type == ReferenceType.MODIFICA

    conformidad = next(r for r in refs if r.target_boe_id == "BOE-A-2015-0500")
    assert conformidad.rel_type == ReferenceType.DE_CONFORMIDAD_CON

    corrige = posteriores[0]
    assert corrige.rel_type == ReferenceType.CORRIGE
    assert corrige.target_boe_id == "BOE-A-2025-2000"


def test_reference_type_mapping():
    assert ReferenceType.from_boe("DEROGA totalmente") == ReferenceType.DEROGA
    assert ReferenceType.from_boe("DESARROLLA el art. 1") == ReferenceType.DESARROLLA
    assert ReferenceType.from_boe(None) == ReferenceType.OTRA
    assert ReferenceType.from_boe("texto raro") == ReferenceType.OTRA


def test_empty_analisis_returns_empty():
    assert parse_references({"data": []}) == []
    assert parse_references({}) == []
