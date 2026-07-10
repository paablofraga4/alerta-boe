"""Generación de subtítulos (SRT) a partir de la narración del guion.

Pura y testeable: reparte el texto en fragmentos legibles y les asigna tiempos
estimando la duración por número de palabras (ritmo de locución configurable).
No necesita ASR: los subtítulos salen del propio guion.
"""

from __future__ import annotations

import re

# Ritmo medio de locución en español (palabras por segundo).
_WORDS_PER_SEC = 2.6
_MAX_WORDS_PER_CUE = 8


def split_into_cues(text: str, max_words: int = _MAX_WORDS_PER_CUE) -> list[str]:
    """Divide el texto en fragmentos cortos, respetando frases cuando puede."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    cues: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i : i + max_words])
            if chunk:
                cues.append(chunk)
    return cues


def _fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(narration: str, words_per_sec: float = _WORDS_PER_SEC) -> str:
    """Construye un SRT con tiempos estimados a partir de la narración."""
    cues = split_into_cues(narration)
    lines: list[str] = []
    t = 0.0
    for idx, cue in enumerate(cues, start=1):
        duration = max(len(cue.split()) / words_per_sec, 1.0)
        start, end = t, t + duration
        lines.append(str(idx))
        lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
        lines.append(cue)
        lines.append("")
        t = end
    return "\n".join(lines)


def estimated_duration(narration: str, words_per_sec: float = _WORDS_PER_SEC) -> float:
    """Duración estimada del vídeo en segundos."""
    words = len(narration.split())
    return round(words / words_per_sec, 1) if words else 0.0
