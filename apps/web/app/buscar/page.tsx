"use client";

import { useState } from "react";
import { api, type SearchHit } from "@/lib/api";
import { DocumentCard } from "@/components/DocumentCard";

export default function BuscarPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.search({ query, limit: 30 });
      setHits(res.results);
      setSearched(true);
    } catch {
      setError("No se ha podido completar la búsqueda.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Buscar en el BOE</h1>
        <p className="text-sm text-gray-500">
          Búsqueda híbrida: combina texto y significado. Prueba
          &ldquo;ayudas a autónomos&rdquo; o &ldquo;transporte escolar&rdquo;.
        </p>
      </div>

      <form onSubmit={onSearch} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="¿Qué te afecta?"
          className="flex-1 rounded-lg border border-gray-300 bg-transparent px-4 py-2 dark:border-gray-700"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-boe-primary px-5 py-2 font-medium text-white disabled:opacity-50"
        >
          {loading ? "Buscando…" : "Buscar"}
        </button>
      </form>

      {error && <p className="rounded bg-red-50 p-4 text-red-700">{error}</p>}

      {searched && !loading && hits.length === 0 && (
        <p className="text-gray-500">Sin resultados para tu búsqueda.</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {hits.map((hit) => (
          <DocumentCard key={hit.document.boe_id} item={hit.document} />
        ))}
      </div>
    </div>
  );
}
