import React from "react";
import {
  AbsoluteFill,
  Audio,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { BoeShortProps } from "./types";

const BG = "linear-gradient(160deg, #1a1a2e 0%, #24243e 60%, #302b63 100%)";
const ACCENT = "#e94560";

function currentCue(props: BoeShortProps, seconds: number): string {
  const cue = props.cues.find((c) => seconds >= c.start && seconds < c.end);
  return cue?.text ?? "";
}

export const BoeShort: React.FC<BoeShortProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;

  // El hook entra con un pequeño rebote y se mantiene arriba.
  const hookIn = spring({ frame, fps, config: { damping: 200 }, durationInFrames: 20 });
  const hookY = interpolate(hookIn, [0, 1], [-40, 0]);

  // Los puntos aparecen escalonados (cada ~1.2 s tras el hook).
  const pointStartFrame = fps * 1.5;
  const perPoint = fps * 1.2;

  // El CTA entra en el último ~15% del vídeo.
  const ctaStart = durationInFrames * 0.85;
  const ctaOpacity = interpolate(frame, [ctaStart, ctaStart + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subtitle = currentCue(props, t);

  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "Inter, system-ui, sans-serif" }}>
      {props.audioFile && <Audio src={staticFile(props.audioFile)} />}

      {/* Etiqueta de fuente */}
      <div style={{ position: "absolute", top: 60, width: "100%", textAlign: "center" }}>
        <span
          style={{
            color: "#fff",
            opacity: 0.6,
            fontSize: 34,
            letterSpacing: 2,
            textTransform: "uppercase",
          }}
        >
          📰 AlertaBOE · {props.boeId}
        </span>
      </div>

      {/* Hook */}
      <div
        style={{
          position: "absolute",
          top: 200,
          width: "100%",
          padding: "0 80px",
          textAlign: "center",
          transform: `translateY(${hookY}px)`,
          opacity: hookIn,
        }}
      >
        <h1 style={{ color: "#fff", fontSize: 88, fontWeight: 800, lineHeight: 1.1, margin: 0 }}>
          {props.hook}
        </h1>
      </div>

      {/* Puntos */}
      <div style={{ position: "absolute", top: 620, width: "100%", padding: "0 90px" }}>
        {props.points.map((point, i) => {
          const start = pointStartFrame + i * perPoint;
          const appear = interpolate(frame, [start, start + 12], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const x = interpolate(appear, [0, 1], [60, 0]);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                gap: 24,
                alignItems: "flex-start",
                marginBottom: 40,
                opacity: appear,
                transform: `translateX(${x}px)`,
              }}
            >
              <span style={{ color: ACCENT, fontSize: 52, fontWeight: 900 }}>›</span>
              <span style={{ color: "#f4f4f8", fontSize: 52, fontWeight: 600, lineHeight: 1.25 }}>
                {point}
              </span>
            </div>
          );
        })}
      </div>

      {/* CTA */}
      <div
        style={{
          position: "absolute",
          bottom: 340,
          width: "100%",
          textAlign: "center",
          opacity: ctaOpacity,
        }}
      >
        <span
          style={{
            display: "inline-block",
            background: ACCENT,
            color: "#fff",
            fontSize: 46,
            fontWeight: 700,
            padding: "20px 44px",
            borderRadius: 999,
          }}
        >
          {props.cta}
        </span>
      </div>

      {/* Subtítulos (karaoke por cue) */}
      {subtitle && (
        <div style={{ position: "absolute", bottom: 140, width: "100%", padding: "0 70px", textAlign: "center" }}>
          <span
            style={{
              color: "#fff",
              fontSize: 50,
              fontWeight: 700,
              background: "rgba(0,0,0,0.55)",
              padding: "12px 24px",
              borderRadius: 16,
              lineHeight: 1.3,
            }}
          >
            {subtitle}
          </span>
        </div>
      )}

      {/* Disclaimer permanente */}
      <div style={{ position: "absolute", bottom: 50, width: "100%", textAlign: "center" }}>
        <span style={{ color: "#fff", opacity: 0.45, fontSize: 26 }}>
          Información divulgativa, no asesoramiento legal.
        </span>
      </div>
    </AbsoluteFill>
  );
};
