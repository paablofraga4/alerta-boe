import type { Metadata } from "next";
import Link from "next/link";
import { api, type Deadline, type TopicCount } from "@/lib/api";
import { Kicker } from "@/components/ScopeBadge";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Radar de plazos · AlertaBOE",
  description: "Ayudas y trámites del BOE con fecha límite, ordenados por urgencia.",
};

function urgencia(dias: number): { label: string; cls: string } {
  if (dias <= 7) return { label: `Quedan ${dias} días`, cls: "bg-crimson text-white" };
  if (dias <= 30)
    return { label: `Quedan ${dias} días`, cls: "bg-crimson/10 text-crimson" };
  return { label: `${dias} días`, cls: "bg-paper text-muted border border-hair" };
}

function fmtFecha(iso: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso + "T00:00:00"));
}

async function load(topic?: string): Promise<{
  deadlines: Deadline[];
  topics: TopicCount[];
} | null> {
  try {
    const [res, { topics }] = await Promise.all([api.deadlines(topic), api.topics()]);
    return { deadlines: res.deadlines, topics: topics.filter((t) => t.count > 0) };
  } catch {
    return null;
  }
}

export default async function RadarPage({
  searchParams,
}: {
  searchParams: { topic?: string };
}) {
  const topic = searchParams.topic;
  const data = await load(topic);

  return (
    <div>
      <header className="border-b border-ink pb-5">
        <p className="kicker">Radar de plazos</p>
        <h1 className="mt-1 font-serif text-4xl font-semibold tracking-tight">
          Lo que caduca, primero
        </h1>
        <p className="mt-2 max-w-2xl text-muted">
          Ayudas, convocatorias y trámites del BOE con fecha límite, extraídos de cada norma
          por los agentes y ordenados por urgencia. Que no se te pase el plazo.
        </p>
      </header>

      {data && data.topics.length > 0 && (
        <div className="mt-5 flex flex-wrap items-center gap-1.5">
          <Link
            href="/radar"
            className={`rounded-sm border px-2.5 py-1 text-sm ${
              !topic ? "border-crimson bg-crimson text-white" : "border-hair bg-card hover:border-crimson"
            }`}
          >
            Todos
          </Link>
          {data.topics.map((t) => (
            <Link
              key={t.slug}
              href={`/radar?topic=${t.slug}`}
              className={`rounded-sm border px-2.5 py-1 text-sm ${
                topic === t.slug
                  ? "border-crimson bg-crimson text-white"
                  : "border-hair bg-card hover:border-crimson"
              }`}
            >
              {t.name}
            </Link>
          ))}
        </div>
      )}

      {!data && (
        <p className="mt-8 rounded-sm border border-hair bg-card p-6 text-muted">
          No se ha podido cargar el radar. Puede que el servicio esté despertando.
        </p>
      )}

      {data && data.deadlines.length === 0 && (
        <div className="mt-8 border border-dashed border-hair p-10 text-center">
          <p className="font-serif text-2xl">Sin plazos abiertos</p>
          <p className="mt-2 text-muted">
            Los plazos aparecen aquí a medida que los agentes leen las publicaciones nuevas.
          </p>
        </div>
      )}

      <ol className="mt-6 space-y-4">
        {data?.deadlines.map((d, i) => {
          const u = urgencia(d.dias_restantes);
          return (
            <li key={`${d.boe_id}-${i}`}>
              <Link
                href={`/documento/${d.boe_id}`}
                className="group flex flex-col gap-2 rounded-sm border border-hair bg-card p-4 transition-colors hover:border-crimson sm:flex-row sm:items-center sm:gap-5"
              >
                <div className="flex shrink-0 flex-col items-start sm:w-44">
                  <span className={`rounded-sm px-2 py-0.5 text-sm font-semibold ${u.cls}`}>
                    ⏳ {u.label}
                  </span>
                  <span className="mt-1 text-xs text-muted">{fmtFecha(d.fecha)}</span>
                </div>
                <div className="min-w-0">
                  <p className="font-serif text-lg font-medium leading-snug group-hover:text-crimson">
                    {d.accion}
                  </p>
                  <div className="mt-1">
                    <Kicker scope={d.scope} extra={d.title.slice(0, 90)} />
                  </div>
                </div>
              </Link>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
