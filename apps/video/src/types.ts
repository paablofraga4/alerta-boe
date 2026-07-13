// Contrato de props que emite boe/content/video/render.py::build_props.

export type Cue = {
  index: number;
  start: number; // segundos
  end: number; // segundos
  text: string;
};

// type (no interface): así satisface la constraint Record<string, unknown> de Remotion.
export type BoeShortProps = {
  boeId: string;
  hook: string;
  points: string[];
  cta: string;
  cues: Cue[];
  narration: string;
  fps: number;
  durationSec: number;
  durationInFrames: number;
  srt: string;
  audioFile?: string; // nombre del mp3 en public/, si se generó
};

export const DEFAULT_PROPS: BoeShortProps = {
  boeId: "BOE-A-2024-0001",
  hook: "¿Sabías esto del BOE?",
  points: [
    "El Gobierno aprueba una nueva ayuda.",
    "Afecta a autónomos y pequeñas empresas.",
    "Hay plazo para solicitarla.",
  ],
  cta: "Síguenos para no perderte ninguna.",
  cues: [
    { index: 1, start: 0, end: 2.5, text: "El Gobierno aprueba una ayuda" },
    { index: 2, start: 2.5, end: 5, text: "para autónomos y pymes." },
  ],
  narration:
    "El Gobierno aprueba una ayuda para autónomos y pymes. Hay plazo para solicitarla.",
  fps: 30,
  durationSec: 8,
  durationInFrames: 240,
  srt: "",
};
