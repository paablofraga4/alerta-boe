/* Tarjeta OG por noticia: al compartir un enlace en WhatsApp/X/LinkedIn sale
 * una tarjeta editorial con el gancho, no un enlace gris. Next la sirve en
 * /documento/<id>/opengraph-image y la enlaza sola en los metadatos. */

import { ImageResponse } from "next/og";
import { api, SCOPE_LABEL } from "@/lib/api";

export const runtime = "nodejs";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "AlertaBOE — el BOE en claro";

const PAPER = "#fbfaf8";
const INK = "#1a1a18";
const MUTED = "#6b6862";
const HAIR = "#e6e2da";
const CRIMSON = "#b11226";

function fmtFecha(iso: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso + "T00:00:00"));
}

export default async function OgImage({ params }: { params: { boeId: string } }) {
  let kicker = "Boletín Oficial del Estado";
  let title = "El BOE, en claro";
  let hook: string | null = null;

  try {
    const doc = await api.document(params.boeId);
    kicker = `${SCOPE_LABEL[doc.scope]} · ${fmtFecha(doc.published_at)}`;
    title = doc.title.length > 160 ? `${doc.title.slice(0, 157)}…` : doc.title;
    const s = doc.summaries[0];
    hook = s?.hook || s?.short || null;
    if (hook && hook.length > 140) hook = `${hook.slice(0, 137)}…`;
  } catch {
    // Sin API: tarjeta genérica de marca.
  }

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
          padding: "56px 64px",
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
            {kicker}
          </div>
          <div
            style={{
              display: "flex",
              marginTop: 24,
              fontSize: title.length > 90 ? 52 : 62,
              lineHeight: 1.12,
              color: INK,
              fontWeight: 700,
            }}
          >
            {title}
          </div>
          {hook && (
            <div
              style={{
                display: "flex",
                marginTop: 28,
                fontSize: 32,
                lineHeight: 1.3,
                color: MUTED,
              }}
            >
              {hook}
            </div>
          )}
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderTop: `2px solid ${HAIR}`,
            paddingTop: 28,
          }}
        >
          <div style={{ display: "flex", fontSize: 40, fontWeight: 900, color: INK }}>
            Alerta<span style={{ color: CRIMSON }}>BOE</span>
          </div>
          <div style={{ display: "flex", fontSize: 24, color: MUTED }}>
            El BOE, en claro
          </div>
        </div>
      </div>
    ),
    size,
  );
}
