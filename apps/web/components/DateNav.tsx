"use client";

import { useRouter } from "next/navigation";

export function DateNav({ fecha }: { fecha: string }) {
  const router = useRouter();
  function shift(days: number) {
    const d = new Date(fecha + "T00:00:00");
    d.setDate(d.getDate() + days);
    router.push(`/?fecha=${d.toISOString().slice(0, 10)}`);
  }
  const btn =
    "rounded-sm border border-hair px-2.5 py-1 text-sm hover:border-ink transition-colors";
  return (
    <div className="flex items-center gap-2">
      <button onClick={() => shift(-1)} className={btn} aria-label="Día anterior">←</button>
      <input
        type="date"
        value={fecha}
        onChange={(e) => router.push(`/?fecha=${e.target.value}`)}
        className="rounded-sm border border-hair bg-transparent px-2 py-1 text-sm"
      />
      <button onClick={() => shift(1)} className={btn} aria-label="Día siguiente">→</button>
    </div>
  );
}
