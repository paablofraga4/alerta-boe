import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { api, SCOPE_LABEL, type DocumentDetail, type Thread } from "@/lib/api";
import { ThreadView } from "@/components/ThreadView";
import { ChatBox } from "@/components/ChatBox";
import { PdfPreview } from "@/components/PdfPreview";

export const dynamic = "force-dynamic";

async function load(boeId: string): Promise<{ doc: DocumentDetail; thread: Thread } | null> {
  try {
    const [doc, thread] = await Promise.all([api.document(boeId), api.thread(boeId)]);
    return { doc, thread };
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { boeId: string };
}): Promise<Metadata> {
  const data = await load(params.boeId);
  if (!data) return { title: "Publicación no encontrada" };
  const short = data.doc.summaries[0]?.short ?? data.doc.title;
  return { title: data.doc.title, description: short };
}

function fmtFecha(iso: string): string {
  return new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long", year: "numeric" }).format(
    new Date(iso + "T00:00:00"),
  );
}

export default async function DocumentoPage({ params }: { params: { boeId: string } }) {
  const data = await load(params.boeId);
  if (!data) notFound();
  const { doc, thread } = data;
  const summary = doc.summaries[0];
  const cuerpo = summary?.long || summary?.short || null;

  return (
    <article>
      <Link href="/" className="text-sm text-muted hover:text-crimson">← Portada</Link>

      <header className="mt-3 border-b border-ink pb-6">
        <p className="kicker">
          {SCOPE_LABEL[doc.scope]}
          <span className="text-muted"> · {fmtFecha(doc.published_at)} · {doc.boe_id}</span>
        </p>
        <h1 className="mt-2 max-w-4xl font-serif text-3xl font-semibold leading-[1.1] tracking-tight sm:text-[2.7rem]">
          {doc.title}
        </h1>
        {doc.departamento && <p className="mt-3 text-muted">{doc.departamento}</p>}
      </header>

      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_minmax(320px,40%)]">
        {/* Columna principal: resumen grande + hilo + chat */}
        <div className="min-w-0">
          <section>
            <h2 className="kicker mb-3">En claro</h2>
            {cuerpo ? (
              <div className="reading font-serif text-ink">
                {cuerpo.split(/\n{2,}/).map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
            ) : (
              <p className="rounded-sm border border-dashed border-hair p-5 text-muted">
                El resumen de esta publicación aún se está generando. Mientras tanto, puedes
                consultar el documento oficial a la derecha.
              </p>
            )}
          </section>

          <section className="mt-12 border-t border-hair pt-8">
            <h2 className="font-serif text-xl font-semibold">El hilo normativo</h2>
            <p className="mb-5 mt-1 text-sm text-muted">De dónde viene esta norma y qué se deriva de ella.</p>
            <ThreadView thread={thread} />
          </section>

          <section className="mt-12 border-t border-hair pt-8">
            <h2 className="font-serif text-xl font-semibold">Pregunta sobre esta norma</h2>
            <p className="mb-4 mt-1 text-sm text-muted">El asistente responde citando el BOE.</p>
            <ChatBox boeId={doc.boe_id} />
          </section>
        </div>

        {/* Barra lateral: PDF oficial + ficha */}
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <PdfPreview url={doc.url_pdf} />

          <div className="mt-5 rounded-sm border border-hair bg-card p-4 text-sm">
            <dl className="space-y-2">
              {doc.rango && (<div className="flex justify-between gap-3"><dt className="text-muted">Rango</dt><dd className="text-right">{doc.rango}</dd></div>)}
              {doc.seccion && (<div className="flex justify-between gap-3"><dt className="text-muted">Sección</dt><dd className="text-right">{doc.seccion}</dd></div>)}
              {doc.epigrafe && (<div className="flex justify-between gap-3"><dt className="text-muted">Epígrafe</dt><dd className="text-right">{doc.epigrafe}</dd></div>)}
            </dl>
            {doc.topics.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5 border-t border-hair pt-3">
                {doc.topics.map((t) => (
                  <span key={t.slug} className="rounded-sm bg-paper px-2 py-0.5 text-xs text-muted">{t.name}</span>
                ))}
              </div>
            )}
            <div className="mt-3 flex flex-wrap gap-4 border-t border-hair pt-3 text-sm">
              {doc.url_html && <a href={doc.url_html} target="_blank" rel="noreferrer" className="text-crimson hover:underline">Texto HTML ↗</a>}
              {doc.url_pdf && <a href={doc.url_pdf} target="_blank" rel="noreferrer" className="text-crimson hover:underline">PDF ↗</a>}
            </div>
          </div>
        </aside>
      </div>
    </article>
  );
}
