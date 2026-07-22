import Link from "next/link";
import { api, type Digest, type DigestItem } from "@/lib/api";
import { HeadlineItem, LeadStory } from "@/components/Headline";
import { DateNav } from "@/components/DateNav";
import { ParaTi } from "@/components/ParaTi";

export const dynamic = "force-dynamic";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

// Emoji por categoría, para escanear la portada de un vistazo.
const CAT_ICON: Record<string, string> = {
  ayudas: "💶",
  normas: "⚖️",
  oposiciones: "🎓",
  otras: "📄",
};

export default async function HomePage({
  searchParams,
}: {
  searchParams: { fecha?: string };
}) {
  const fecha = searchParams.fecha ?? today();

  let digest: Digest | null = null;
  let error = false;
  try {
    digest = await api.digest(fecha);
  } catch {
    error = true;
  }

  const lead = digest?.highlights?.[0] ?? null;
  const leadId = lead?.boe_id;

  return (
    <div>
      <div className="mb-6 flex items-end justify-between gap-4 border-b border-hair pb-3">
        <h1 className="kicker !text-ink">Portada del día</h1>
        <DateNav fecha={fecha} />
      </div>

      {error && (
        <p className="rounded-sm border border-hair bg-card p-6 text-muted">
          No se ha podido cargar el BOE. Es posible que el servicio esté despertando
          (tarda unos segundos la primera vez) o que aún no se haya ingerido este día.
        </p>
      )}

      {digest && digest.total === 0 && !error && (
        <div className="border border-dashed border-hair p-10 text-center">
          <p className="font-serif text-2xl">Sin publicaciones para el {fecha}</p>
          <p className="mt-2 text-muted">
            Puede ser fin de semana o festivo, o que todavía no se haya procesado el día.
          </p>
        </div>
      )}

      {lead && (
        <section className="mb-10 border-b border-ink pb-10">
          <LeadStory item={lead} />
        </section>
      )}

      <ParaTi />

      {/* Categorías de valor: ayudas, normas, oposiciones... ordenadas por relevancia */}
      {digest?.categories?.map((group) => {
        const items = group.items.filter((it) => it.boe_id !== leadId);
        if (items.length === 0) return null;
        return (
          <section key={group.category} className="mb-10">
            <div className="mb-2 flex items-baseline justify-between gap-3 border-b border-hair pb-1">
              <h2 className="flex items-baseline gap-2 font-serif text-xl font-semibold">
                <span>{CAT_ICON[group.category] ?? "📄"}</span>
                {group.label}
                <span className="text-sm font-normal text-muted">{group.count}</span>
              </h2>
              {group.count > items.length && (
                <Link
                  href={`/buscar?category=${group.category}`}
                  className="text-sm font-medium text-crimson hover:underline"
                >
                  Ver todo →
                </Link>
              )}
            </div>
            <div className="grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((item: DigestItem) => (
                <HeadlineItem key={item.boe_id} item={item} />
              ))}
            </div>
          </section>
        );
      })}

      {/* Ruido colapsado: nombramientos, edictos, anuncios — recuento, no lista */}
      {digest?.noise && digest.noise.total > 0 && (
        <details className="mb-10 rounded-sm border border-hair bg-card p-4">
          <summary className="cursor-pointer select-none font-serif text-base font-medium text-muted">
            + {digest.noise.total} publicaciones de trámite
            <span className="ml-2 text-sm font-normal">
              (nombramientos, edictos, anuncios) — normalmente sin interés general
            </span>
          </summary>
          <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1 border-t border-hair pt-3 text-sm text-muted">
            {Object.entries(digest.noise.breakdown).map(([cat, n]) => (
              <li key={cat}>
                {NOISE_LABEL[cat] ?? cat}: <span className="text-ink">{n}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

const NOISE_LABEL: Record<string, string> = {
  nombramientos: "Nombramientos y ceses",
  justicia: "Edictos y justicia",
  anuncios: "Contratación y anuncios",
};
