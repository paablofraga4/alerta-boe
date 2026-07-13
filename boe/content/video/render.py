"""Render de vídeo para TikTok/Reels: narración (TTS) + subtítulos + props.

Estrategia (F5):
  - TTS con `edge-tts` (gratis, voces es-ES). Import perezoso: si no está,
    se generan solo los subtítulos y las props, y el audio queda pendiente.
  - Los subtítulos salen del guion (`subtitles.build_srt`), sin ASR.
  - Se emite un `props.json` con hook/puntos/CTA/subtítulos: es la entrada de una
    plantilla **Remotion** (React → mp4) que compone titular, bullets animados y
    subtítulos karaoke sobre un fondo de marca. El ensamblado final del mp4 lo
    hace Remotion en el paso de render (documentado en infra), no este módulo.

Así, el 90% del trabajo (guion, voz y subtítulos) queda hecho y reproducible; el
render visual es un paso determinista sobre estos artefactos.
"""

from __future__ import annotations

import json
from pathlib import Path

from boe.content.video.subtitles import build_cues, build_srt, estimated_duration

DEFAULT_VOICE = "es-ES-AlvaroNeural"
DEFAULT_FPS = 30
# Colchón al final para el CTA (segundos) tras terminar la narración.
_TAIL_SEC = 2.0


def build_props(
    boe_id: str,
    hook: str,
    points: list[str],
    cta: str,
    narration: str,
    *,
    fps: int = DEFAULT_FPS,
) -> dict:
    """Props para la plantilla de vídeo Remotion.

    Contiene todo lo que la composición `BoeShort` necesita para renderizar sin
    parsear nada: textos, subtítulos con tiempos, duración y frames.
    """
    duration_sec = estimated_duration(narration) + _TAIL_SEC
    return {
        "boeId": boe_id,
        "hook": hook,
        "points": points,
        "cta": cta,
        "cues": build_cues(narration),
        "narration": narration,
        "fps": fps,
        "durationSec": round(duration_sec, 1),
        "durationInFrames": max(int(duration_sec * fps), fps),
        "srt": build_srt(narration),
    }


async def synth_narration(narration: str, out_path: Path, voice: str = DEFAULT_VOICE) -> bool:
    """Genera el audio de la narración con edge-tts. True si se creó el mp3."""
    try:
        import edge_tts  # import perezoso: extra opcional
    except ImportError:  # pragma: no cover
        return False
    communicate = edge_tts.Communicate(narration, voice)
    await communicate.save(str(out_path))  # pragma: no cover
    return True


async def render_assets(post_id: int, props: dict, out_dir: Path) -> dict:
    """Escribe props.json y el SRT (y el audio si edge-tts está disponible)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    props_path = out_dir / f"{post_id}.props.json"
    srt_path = out_dir / f"{post_id}.srt"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
    srt_path.write_text(props["srt"], encoding="utf-8")

    audio_path = out_dir / f"{post_id}.mp3"
    narration = props.get("narration") or props.get("srt", "")
    has_audio = await synth_narration(narration, audio_path)

    if has_audio:
        # La plantilla Remotion carga el audio vía staticFile(audioFile).
        props["audioFile"] = audio_path.name
        props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "props": str(props_path),
        "srt": str(srt_path),
        "audio": str(audio_path) if has_audio else None,
    }
