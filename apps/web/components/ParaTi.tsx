"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, type Document, type TopicCount } from "@/lib/api";
import { HeadlineItem } from "@/components/Headline";

const STORAGE_KEY = "alertaboe:temas";

function loadSaved(): string[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

/** Portada personalizada: eliges tus temas (se guardan en tu navegador) y ves
 * primero lo que te afecta, ordenado por relevancia semántica. */
export function ParaTi() {
  const [topics, setTopics] = useState<TopicCount[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setSelected(loadSaved());
    api.topics().then((res) => setTopics(res.topics.filter((t) => t.count > 0))).catch(() => {});
  }, []);

  const fetchDocs = useCallback(async (slugs: string[]) => {
    if (slugs.length === 0) {
      setDocs([]);
      return;
    }
    setLoading(true);
    try {
      const results = await Promise.all(
        slugs.map((slug) => api.search({ query: "", topic: slug, limit: 6 })),
      );
      const seen = new Set<string>();
      const merged: Document[] = [];
      for (const res of results) {
        for (const hit of res.results) {
          if (!seen.has(hit.document.boe_id)) {
            seen.add(hit.document.boe_id);
            merged.push(hit.document);
          }
        }
      }
      merged.sort((a, b) => (a.published_at < b.published_at ? 1 : -1));
      setDocs(merged.slice(0, 9));
    } catch {
      setDocs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocs(selected);
  }, [selected, fetchDocs]);

  function toggle(slug: string) {
    const next = selected.includes(slug)
      ? selected.filter((s) => s !== slug)
      : [...selected, slug];
    setSelected(next);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }

  const selectedNames = topics.filter((t) => selected.includes(t.slug));

  return (
    <section className="mb-10 rounded-sm border border-hair bg-card p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div className="flex items-baseline gap-3">
          <h2 className="font-serif text-lg font-semibold">Para ti</h2>
          {selectedNames.length > 0 && (
            <span className="text-sm text-muted">
              {selectedNames.map((t) => t.name).join(" · ")}
            </span>
          )}
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          className="text-sm font-medium text-crimson hover:underline"
        >
          {open ? "Cerrar" : selected.length ? "Editar mis temas" : "Elegir mis temas"}
        </button>
      </div>

      {open && (
        <div className="mt-3 flex flex-wrap gap-1.5 border-t border-hair pt-3">
          {topics.map((t) => {
            const active = selected.includes(t.slug);
            return (
              <button
                key={t.slug}
                onClick={() => toggle(t.slug)}
                className={`rounded-sm border px-2.5 py-1 text-sm transition-colors ${
                  active
                    ? "border-crimson bg-crimson text-white"
                    : "border-hair bg-paper text-ink hover:border-crimson"
                }`}
              >
                {t.name}
              </button>
            );
          })}
          {topics.length === 0 && (
            <p className="text-sm text-muted">Los temas aparecerán cuando haya datos ingeridos.</p>
          )}
        </div>
      )}

      {selected.length === 0 && !open && (
        <p className="mt-2 text-sm text-muted">
          Elige tus temas (ayudas, empleo público, sanidad...) y verás aquí primero lo que te
          afecta. Se guarda solo en tu navegador.
        </p>
      )}

      {loading && <p className="mt-3 text-sm text-muted">Cargando tu selección…</p>}

      {!loading && selected.length > 0 && docs.length === 0 && (
        <p className="mt-3 text-sm text-muted">
          Nada reciente en tus temas. Prueba a añadir alguno más o{" "}
          <Link href="/buscar" className="text-crimson hover:underline">busca directamente</Link>.
        </p>
      )}

      {docs.length > 0 && (
        <div className="mt-2 grid gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((d) => (
            <HeadlineItem key={d.boe_id} item={d} />
          ))}
        </div>
      )}
    </section>
  );
}
