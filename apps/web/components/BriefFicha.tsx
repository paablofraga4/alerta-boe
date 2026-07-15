import type { SummaryStructured } from "@/lib/api";

/** Ficha "en claro" del agente por documento: qué regula, a quién afecta,
 * puntos clave, plazos y qué hacer. Solo pinta las secciones con contenido. */
export function BriefFicha({ data }: { data: SummaryStructured }) {
  const afecta = data.a_quien_afecta ?? [];
  const puntos = data.puntos_clave ?? [];
  const plazos = data.plazos ?? [];
  const hacer = data.que_hacer ?? [];

  const vacio =
    !data.que_regula && !afecta.length && !puntos.length && !plazos.length && !hacer.length;
  if (vacio) return null;

  return (
    <div className="mt-8 space-y-6 border-t border-hair pt-8">
      {data.que_regula && (
        <div>
          <h3 className="kicker mb-2">Qué regula</h3>
          <p className="font-serif text-lg leading-snug text-ink">{data.que_regula}</p>
        </div>
      )}

      {puntos.length > 0 && (
        <div>
          <h3 className="kicker mb-2">Puntos clave</h3>
          <ul className="space-y-1.5">
            {puntos.map((p, i) => (
              <li key={i} className="flex gap-2 text-ink">
                <span className="mt-1 text-crimson">▪</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {afecta.length > 0 && (
        <div>
          <h3 className="kicker mb-2">A quién afecta</h3>
          <div className="flex flex-wrap gap-1.5">
            {afecta.map((a, i) => (
              <span key={i} className="rounded-sm border border-hair bg-card px-2 py-0.5 text-sm">
                {a}
              </span>
            ))}
          </div>
        </div>
      )}

      {plazos.length > 0 && (
        <div>
          <h3 className="kicker mb-2">Fechas y plazos</h3>
          <ul className="space-y-2">
            {plazos.map((p, i) => (
              <li key={i} className="flex gap-3 border-l-2 border-crimson pl-3">
                <span className="font-serif font-semibold text-ink">{p.fecha}</span>
                <span className="text-muted">{p.accion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {hacer.length > 0 && (
        <div className="rounded-sm border border-hair bg-card p-4">
          <h3 className="kicker mb-2">Qué puedes hacer</h3>
          <ul className="space-y-1.5">
            {hacer.map((h, i) => (
              <li key={i} className="flex gap-2 text-ink">
                <span className="mt-0.5 text-crimson">→</span>
                <span>{h}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
