"""Subtítulos SRT a partir de la narración: puro, testeable sin dependencias."""

from boe.content.video.subtitles import build_srt, estimated_duration, split_into_cues


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
