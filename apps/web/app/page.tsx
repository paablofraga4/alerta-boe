import { api, SCOPE_LABEL, type Digest, type DigestItem } from "@/lib/api";
import { HeadlineItem, LeadStory } from "@/components/Headline";
import { DateNav } from "@/components/DateNav";

export const dynamic = "force-dynamic";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

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

      {digest?.groups.map((group) => {
        const items = group.items.filter((it) => it.boe_id !== leadId);
        if (items.length === 0) return null;
        return (
          <section key={group.scope} className="mb-10">
            <div className="mb-1 flex items-baseline gap-3">
              <h2 className="font-serif text-lg font-semibold">{SCOPE_LABEL[group.scope]}</h2>
              <span className="text-sm text-muted">{group.count}</span>
            </div>
            <div className="grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((item: DigestItem) => (
                <HeadlineItem key={item.boe_id} item={item} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
