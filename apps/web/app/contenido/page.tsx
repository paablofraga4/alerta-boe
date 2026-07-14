"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type ContentPost, type ContentStatus } from "@/lib/api";
import { ContentCard } from "@/components/ContentCard";

const FILTERS: { label: string; value: ContentStatus | "" }[] = [
  { label: "Borradores", value: "draft" },
  { label: "Aprobados", value: "approved" },
  { label: "Publicados", value: "published" },
  { label: "Todos", value: "" },
];

export default function ContenidoPage() {
  const [status, setStatus] = useState<ContentStatus | "">("draft");
  const [posts, setPosts] = useState<ContentPost[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.content(status || undefined);
      setPosts(res.posts);
    } catch {
      setError("No se ha podido cargar la cola (¿está la API en marcha?).");
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    load();
  }, [load]);

  async function act(id: number, fn: (id: number) => Promise<ContentPost>) {
    setBusyId(id);
    try {
      const updated = await fn(id);
      setPosts((prev) =>
        prev
          .map((p) => (p.id === id ? updated : p))
          // Si el filtro es por estado, saca de la lista lo que ya no encaja.
          .filter((p) => !status || p.status === status),
      );
    } catch {
      setError("La acción no se pudo completar.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Cola de contenido</h1>
        <p className="text-sm text-gray-500">
          Revisa, aprueba y publica las piezas generadas para redes. Nada se
          publica sin tu visto bueno.
        </p>
      </div>

      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value || "all"}
            onClick={() => setStatus(f.value)}
            className={`rounded-full px-3 py-1 text-sm ${
              status === f.value
                ? "bg-crimson text-white"
                : "border border-gray-300 dark:border-gray-700"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <p className="rounded bg-red-50 p-4 text-red-700">{error}</p>}
      {loading && <p className="text-gray-500">Cargando…</p>}
      {!loading && posts.length === 0 && (
        <p className="rounded border border-dashed border-gray-300 p-8 text-center text-gray-500 dark:border-gray-700">
          No hay piezas en este estado. Genera borradores con{" "}
          <code>boe content-generate &lt;fecha&gt;</code>.
        </p>
      )}

      <div className="grid gap-3">
        {posts.map((post) => (
          <ContentCard
            key={post.id}
            post={post}
            busy={busyId === post.id}
            onApprove={() => act(post.id, api.approve)}
            onReject={() => act(post.id, api.reject)}
            onPublish={() => act(post.id, api.publish)}
          />
        ))}
      </div>
    </div>
  );
}
