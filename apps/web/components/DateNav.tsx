"use client";

import { useRouter } from "next/navigation";

export function DateNav({ fecha }: { fecha: string }) {
  const router = useRouter();

  function shift(days: number) {
    const d = new Date(fecha + "T00:00:00");
    d.setDate(d.getDate() + days);
    router.push(`/?fecha=${d.toISOString().slice(0, 10)}`);
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => shift(-1)}
        className="rounded border border-gray-300 px-2 py-1 text-sm hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
        aria-label="Día anterior"
      >
        ← Anterior
      </button>
      <input
        type="date"
        value={fecha}
        onChange={(e) => router.push(`/?fecha=${e.target.value}`)}
        className="rounded border border-gray-300 bg-transparent px-2 py-1 text-sm dark:border-gray-700"
      />
      <button
        onClick={() => shift(1)}
        className="rounded border border-gray-300 px-2 py-1 text-sm hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
        aria-label="Día siguiente"
      >
        Siguiente →
      </button>
    </div>
  );
}
