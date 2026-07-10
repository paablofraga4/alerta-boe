import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { api, type DocumentDetail, type Thread } from "@/lib/api";
import { ScopeBadge } from "@/components/ScopeBadge";
import { ThreadView } from "@/components/ThreadView";
import { ChatBox } from "@/components/ChatBox";

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

export default async function DocumentoPage({ params }: { params: { boeId: string } }) {
  const data = await load(params.boeId);
  if (!data) notFound();
  const { doc, thread } = data;
  const summary = doc.summaries[0];

  return (
    <article className="space-y-8">
      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <ScopeBadge scope={doc.scope} />
          {doc.topics.map((t) => (
            <span
              key={t.slug}
              className="rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-gray-800"
            >
              {t.name}
            </span>
          ))}
          <span className="text-xs text-gray-400">
            {doc.published_at} · {doc.boe_id}
          </span>
        </div>
        <h1 className="text-2xl font-bold leading-tight">{doc.title}</h1>
        {doc.departamento && (
          <p className="text-sm text-gray-500">{doc.departamento}</p>
        )}
      </header>

      {summary?.long && (
        <section className="rounded-lg bg-white p-5 dark:bg-gray-900">
          <h2 className="mb-2 text-lg font-semibold">En claro</h2>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{summary.long}</p>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold">El hilo normativo</h2>
        <p className="mb-4 text-sm text-gray-500">
          De dónde viene esta norma y qué se deriva de ella.
        </p>
        <ThreadView thread={thread} />
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Pregunta sobre esta norma</h2>
        <ChatBox boeId={doc.boe_id} />
      </section>

      <section className="flex gap-4 text-sm">
        {doc.url_html && (
          <a href={doc.url_html} className="text-boe-accent underline" target="_blank" rel="noreferrer">
            Ver texto original (HTML)
          </a>
        )}
        {doc.url_pdf && (
          <a href={doc.url_pdf} className="text-boe-accent underline" target="_blank" rel="noreferrer">
            PDF oficial
          </a>
        )}
      </section>
    </article>
  );
}
