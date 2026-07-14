"use client";

import { useState } from "react";
import { api, type SearchHit } from "@/lib/api";
import { HeadlineItem } from "@/components/Headline";

export default function BuscarPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(false);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(false);
    try {
      const res = await api.search({ query, limit: 30 });
      setHits(res.results);
      setSearched(true);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="font-serif text-3xl font-semibold">Buscar en el BOE</h1>
      <p className="mt-1 text-muted">
        Búsqueda que combina texto y significado. Prueba «ayudas a autónomos» o «transporte escolar».
      </p>

      <form onSubmit={onSearch} className="mt-6 flex gap-2 border-b-2 border-ink pb-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="¿Qué te afecta?"
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

      {error && <p className="mt-6 text-crimson">No se ha podido completar la búsqueda.</p>}
      {searched && !loading && hits.length === 0 && (
        <p className="mt-6 text-muted">Sin resultados para tu búsqueda.</p>
      )}

      <div className="mt-4 grid gap-x-8 sm:grid-cols-2">
        {hits.map((hit) => (
          <HeadlineItem key={hit.document.boe_id} item={hit.document} />
        ))}
      </div>
    </div>
  );
}
