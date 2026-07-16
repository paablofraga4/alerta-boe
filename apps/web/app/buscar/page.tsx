"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, SCOPE_LABEL, type Scope, type SearchHit, type TopicCount } from "@/lib/api";
import { HeadlineItem } from "@/components/Headline";

const SCOPES: Scope[] = ["nacional", "autonomico", "europeo", "otro"];

function Buscador() {
  const params = useSearchParams();
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [topics, setTopics] = useState<TopicCount[]>([]);
  const [topic, setTopic] = useState<string>(params.get("topic") ?? "");
  const [scope, setScope] = useState<Scope | "">("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.topics().then((res) => setTopics(res.topics.filter((t) => t.count > 0))).catch(() => {});
  }, []);

  async function run(over?: { topic?: string; scope?: Scope | "" }) {
    const t = over?.topic ?? topic;
    const s = over?.scope ?? scope;
    setLoading(true);
    setError(false);
    try {
      const res = await api.search({
        query,
        limit: 30,
        topic: t || undefined,
        scope: s || undefined,
        desde: desde || undefined,
        hasta: hasta || undefined,
      });
      setHits(res.results);
      setSearched(true);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  // Si llega con ?topic= o ?q= (p. ej. desde una ficha), busca al entrar.
  useEffect(() => {
    if (params.get("topic") || params.get("q")) run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSearch(e: React.FormEvent) {
    e.preventDefault();
    run();
  }

  return (
    <div>
      <h1 className="font-serif text-3xl font-semibold">Buscar en el BOE</h1>
      <p className="mt-1 text-muted">
        Búsqueda por significado, no solo por palabras. Combínala con los filtros: tema, ámbito y fechas.
      </p>

      <form onSubmit={onSearch} className="mt-6 flex gap-2 border-b-2 border-ink pb-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="¿Qué te afecta? («ayudas a autónomos», «oposiciones sanidad»...)"
          className="flex-1 bg-transparent px-1 py-2 font-serif text-xl outline-none placeholder:text-muted"
          autoFocus
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-sm bg-crimson px-5 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? "…" : "Buscar"}
        </button>
      </form>

      {/* Temas */}
      {topics.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          <span className="kicker mr-1">Tema</span>
          {topics.map((t) => {
            const active = topic === t.slug;
            return (
              <button
                key={t.slug}
                onClick={() => {
                  const next = active ? "" : t.slug;
                  setTopic(next);
                  run({ topic: next });
                }}
                className={`rounded-sm border px-2.5 py-1 text-sm transition-colors ${
                  active
                    ? "border-crimson bg-crimson text-white"
                    : "border-hair bg-card text-ink hover:border-crimson"
                }`}
              >
                {t.name} <span className={active ? "text-white/70" : "text-muted"}>{t.count}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Ámbito + fechas */}
      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
        <div className="flex items-center gap-1.5">
          <span className="kicker mr-1">Ámbito</span>
          {SCOPES.map((s) => {
            const active = scope === s;
            return (
              <button
                key={s}
                onClick={() => {
                  const next = active ? "" : s;
                  setScope(next);
                  run({ scope: next });
                }}
                className={`rounded-sm border px-2.5 py-1 transition-colors ${
                  active
                    ? "border-crimson bg-crimson text-white"
                    : "border-hair bg-card text-ink hover:border-crimson"
                }`}
              >
                {SCOPE_LABEL[s]}
              </button>
            );
          })}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="kicker mr-1">Entre</span>
          <input
            type="date"
            value={desde}
            onChange={(e) => setDesde(e.target.value)}
            className="rounded-sm border border-hair bg-card px-2 py-1"
          />
          <span className="text-muted">y</span>
          <input
            type="date"
            value={hasta}
            onChange={(e) => setHasta(e.target.value)}
            className="rounded-sm border border-hair bg-card px-2 py-1"
          />
        </div>
      </div>

      {error && <p className="mt-6 text-crimson">No se ha podido completar la búsqueda.</p>}
      {searched && !loading && hits.length === 0 && (
        <p className="mt-6 text-muted">Sin resultados con esos filtros.</p>
      )}

      <div className="mt-4 grid gap-x-8 sm:grid-cols-2">
        {hits.map((hit) => (
          <HeadlineItem key={hit.document.boe_id} item={hit.document} />
        ))}
      </div>
    </div>
  );
}

export default function BuscarPage() {
  return (
    <Suspense>
      <Buscador />
    </Suspense>
  );
}
