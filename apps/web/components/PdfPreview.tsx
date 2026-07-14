"use client";

import { useState } from "react";

// Preview del PDF oficial del BOE. Si el navegador/host no permite embeberlo,
// muestra un enlace de respaldo.
export function PdfPreview({ url }: { url: string | null }) {
  const [failed, setFailed] = useState(false);
  if (!url) {
    return (
      <div className="flex h-64 items-center justify-center border border-hair text-sm text-muted">
        Sin PDF oficial disponible.
      </div>
    );
  }
  return (
    <figure className="overflow-hidden rounded-sm border border-hair bg-card">
      <figcaption className="flex items-center justify-between border-b border-hair px-3 py-2 text-[0.7rem] uppercase tracking-wider text-muted">
        <span>Documento oficial · PDF</span>
        <a href={url} target="_blank" rel="noreferrer" className="text-crimson hover:underline">
          Abrir ↗
        </a>
      </figcaption>
      {failed ? (
        <div className="flex h-72 flex-col items-center justify-center gap-2 p-6 text-center text-sm text-muted">
          <p>La vista previa no se puede mostrar aquí.</p>
          <a href={url} target="_blank" rel="noreferrer" className="font-medium text-crimson hover:underline">
            Ver el PDF en boe.es ↗
          </a>
        </div>
      ) : (
        <iframe
          src={`${url}#view=FitH`}
          title="PDF oficial del BOE"
          className="h-[70vh] w-full bg-white"
          onError={() => setFailed(true)}
        />
      )}
    </figure>
  );
}
