/* Tarjeta OG por defecto del sitio (portada, radar, buscar...). */

import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "AlertaBOE — el BOE en claro";

const PAPER = "#fbfaf8";
const INK = "#1a1a18";
const MUTED = "#6b6862";
const HAIR = "#e6e2da";
const CRIMSON = "#b11226";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          backgroundColor: PAPER,
          padding: "64px 72px",
          fontFamily: "Georgia, serif",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              display: "flex",
              fontSize: 26,
              letterSpacing: 3,
              textTransform: "uppercase",
              color: CRIMSON,
              fontWeight: 700,
            }}
          >
            Boletín Oficial del Estado · cada día, en claro
          </div>
          <div
            style={{
              display: "flex",
              marginTop: 30,
              fontSize: 96,
              fontWeight: 900,
              color: INK,
            }}
          >
            Alerta<span style={{ color: CRIMSON }}>BOE</span>
          </div>
          <div style={{ display: "flex", marginTop: 26, fontSize: 36, color: MUTED, lineHeight: 1.35 }}>
            Titulares en lenguaje humano, radar de plazos y ayudas, y el hilo de cada norma.
          </div>
        </div>
        <div
          style={{
            display: "flex",
            borderTop: `2px solid ${HAIR}`,
            paddingTop: 28,
            fontSize: 26,
            color: MUTED,
          }}
        >
          ⏳ Que no se te pase un plazo · 💶 Que no se te escape una ayuda
        </div>
      </div>
    ),
    size,
  );
}
