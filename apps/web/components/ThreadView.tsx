import Link from "next/link";
import type { Reference, Thread } from "@/lib/api";

const REL_LABEL: Record<string, string> = {
  modifica: "Modifica",
  deroga: "Deroga",
  desarrolla: "Desarrolla",
  prorroga: "Prorroga",
  corrige: "Corrige",
  cita: "Cita",
  de_conformidad_con: "De conformidad con",
  otra: "Relacionada",
};

function RefRow({ reference }: { reference: Reference }) {
  const label = REL_LABEL[reference.rel_type] ?? reference.rel_type;
  const title = reference.target_title ?? reference.target_boe_id ?? "Norma referenciada";
  return (
    <li className="flex flex-col gap-1 border-l-2 border-gray-200 py-2 pl-3 dark:border-gray-700">
      <span className="inline-block w-fit rounded bg-boe-accent/10 px-2 py-0.5 text-xs font-medium text-boe-accent">
        {label}
      </span>
      {reference.target_boe_id ? (
        <Link href={`/documento/${reference.target_boe_id}`} className="text-sm hover:underline">
          {title}
        </Link>
      ) : (
        <span className="text-sm text-gray-600 dark:text-gray-400">{title}</span>
      )}
    </li>
  );
}

export function ThreadView({ thread }: { thread: Thread }) {
  const nada = thread.anteriores.length === 0 && thread.posteriores.length === 0;
  if (nada) {
    return (
      <p className="text-sm text-gray-500">
        No se han detectado precedentes ni normas derivadas para esta publicación.
      </p>
    );
  }
  return (
    <div className="grid gap-6 sm:grid-cols-2">
      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-500">
          ← Precedentes ({thread.anteriores.length})
        </h3>
        <ul className="space-y-1">
          {thread.anteriores.map((r, i) => (
            <RefRow key={`a-${i}`} reference={r} />
          ))}
          {thread.anteriores.length === 0 && (
            <li className="text-sm text-gray-400">Sin precedentes.</li>
          )}
        </ul>
      </div>
      <div>
        <h3 className="mb-2 text-sm font-semibold text-gray-500">
          Derivadas ({thread.posteriores.length}) →
        </h3>
        <ul className="space-y-1">
          {thread.posteriores.map((r, i) => (
            <RefRow key={`p-${i}`} reference={r} />
          ))}
          {thread.posteriores.length === 0 && (
            <li className="text-sm text-gray-400">Sin normas derivadas.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
