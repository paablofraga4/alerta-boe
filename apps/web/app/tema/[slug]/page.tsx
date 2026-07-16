import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { HeadlineItem } from "@/components/Headline";

export const dynamic = "force-dynamic";

async function loadTopic(slug: string) {
  try {
    const [{ topics }, res] = await Promise.all([
      api.topics(),
      api.search({ query: "", topic: slug, limit: 40 }),
    ]);
    const topic = topics.find((t) => t.slug === slug);
    if (!topic) return null;
    return { topic, hits: res.results };
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}): Promise<Metadata> {
  const data = await loadTopic(params.slug);
  return { title: data ? `${data.topic.name} · AlertaBOE` : "Tema" };
}

export default async function TemaPage({ params }: { params: { slug: string } }) {
  const data = await loadTopic(params.slug);
  if (!data) notFound();
  const { topic, hits } = data;

  return (
    <div>
      <Link href="/" className="text-sm text-muted hover:text-crimson">← Portada</Link>
      <header className="mt-3 border-b border-ink pb-5">
        <p className="kicker">Tema</p>
        <h1 className="mt-1 font-serif text-4xl font-semibold tracking-tight">{topic.name}</h1>
        <p className="mt-2 text-muted">
          {topic.count} publicaciones. Lo más reciente primero.{" "}
          <Link href={`/buscar?topic=${topic.slug}`} className="text-crimson hover:underline">
            Buscar dentro del tema →
          </Link>
        </p>
      </header>

      {hits.length === 0 ? (
        <p className="mt-8 text-muted">Todavía no hay publicaciones en este tema.</p>
      ) : (
        <div className="mt-2 grid gap-x-8 sm:grid-cols-2">
          {hits.map((hit) => (
            <HeadlineItem key={hit.document.boe_id} item={hit.document} />
          ))}
        </div>
      )}
    </div>
  );
}
