"""Subtítulos SRT a partir de la narración: puro, testeable sin dependencias."""

from boe.content.video.render import build_props
from boe.content.video.subtitles import (
    build_cues,
    build_srt,
    estimated_duration,
    split_into_cues,
)


def test_split_into_cues_respects_max_words():
    text = "Una frase con varias palabras aquí. Otra frase distinta también larga."
    cues = split_into_cues(text, max_words=4)
    assert all(len(c.split()) <= 4 for c in cues)
    assert cues  # no vacío


def test_build_srt_structure():
    srt = build_srt("El Gobierno aprueba ayudas. Los autónomos pueden solicitarlas ya.")
    # Formato SRT: índice, línea de tiempos con '-->', texto.
    assert "1\n" in srt
    assert "-->" in srt
    assert "00:00:00,000" in srt


def test_estimated_duration_scales_with_words():
    corto = estimated_duration("una dos tres")
    largo = estimated_duration(" ".join(["palabra"] * 100))
    assert largo > corto
    assert estimated_duration("") == 0.0


def test_build_cues_are_ordered_and_timed():
    cues = build_cues("El Gobierno aprueba ayudas. Los autónomos pueden pedirlas ya.")
    assert cues
    # Tiempos monótonos y no solapados.
    for a, b in zip(cues, cues[1:], strict=False):
        assert a["end"] <= b["start"] + 1e-6
        assert a["start"] < a["end"]


def test_build_props_matches_remotion_contract():
    props = build_props(
        "BOE-A-2024-0001",
        hook="¿Sabías esto?",
        points=["p1", "p2", "p3"],
        cta="Síguenos",
        narration="El Gobierno aprueba una ayuda para autónomos y pymes.",
        fps=30,
    )
    # Claves que consume la plantilla src/types.ts (BoeShortProps).
    for key in ("boeId", "hook", "points", "cta", "cues", "fps",
                "durationInFrames", "durationSec", "srt"):
        assert key in props
    assert props["durationInFrames"] >= props["fps"]
    assert isinstance(props["cues"], list)
