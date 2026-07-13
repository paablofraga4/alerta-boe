import { api, SCOPE_LABEL, type Digest } from "@/lib/api";
import { DocumentCard } from "@/components/DocumentCard";
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
  let error: string | null = null;
  try {
    digest = await api.digest(fecha);
  } catch {
    error = "No se ha podido cargar el BOE (¿está la API en marcha?).";
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">El BOE de hoy, en claro</h1>
          <p className="text-sm text-gray-500">
            Publicaciones oficiales del {fecha}, resumidas y agrupadas.
          </p>
        </div>
        <DateNav fecha={fecha} />
      </section>

      {error && <p className="rounded bg-red-50 p-4 text-red-700">{error}</p>}

      {digest && digest.total === 0 && (
        <p className="rounded border border-dashed border-gray-300 p-8 text-center text-gray-500 dark:border-gray-700">
          No hay publicaciones del BOE para esta fecha (puede ser fin de semana o
          festivo, o aún no se ha ingerido).
        </p>
      )}

      {digest && digest.highlights.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Destacados</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {digest.highlights.map((item) => (
              <DocumentCard key={item.boe_id} item={item} />
            ))}
          </div>
        </section>
      )}

      {digest &&
        digest.groups.map((group) => (
          <section key={group.scope}>
            <h2 className="mb-3 text-lg font-semibold">
              {SCOPE_LABEL[group.scope]}{" "}
              <span className="text-sm font-normal text-gray-400">
                ({group.count})
              </span>
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {group.items.map((item) => (
                <DocumentCard key={item.boe_id} item={item} />
              ))}
            </div>
          </section>
        ))}
    </div>
  );
}
