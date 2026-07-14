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

function Row({ reference }: { reference: Reference }) {
  const label = REL_LABEL[reference.rel_type] ?? reference.rel_type;
  const title = reference.target_title ?? reference.target_boe_id ?? "Norma referenciada";
  return (
    <li className="border-l-2 border-hair py-2 pl-4">
      <span className="kicker">{label}</span>
      <div className="mt-0.5">
        {reference.target_boe_id ? (
          <Link href={`/documento/${reference.target_boe_id}`} className="text-sm hover:text-crimson">
            {title}
          </Link>
        ) : (
          <span className="text-sm text-muted">{title}</span>
        )}
      </div>
    </li>
  );
}

export function ThreadView({ thread }: { thread: Thread }) {
  const vacio = thread.anteriores.length === 0 && thread.posteriores.length === 0;
  if (vacio) {
    return (
      <p className="text-sm text-muted">
        No se han detectado precedentes ni normas derivadas para esta publicación.
      </p>
    );
  }
  return (
    <div className="grid gap-8 sm:grid-cols-2">
      <div>
        <p className="mb-2 font-serif text-sm font-semibold text-muted">
          Precedentes ({thread.anteriores.length})
        </p>
        <ul className="space-y-1">
          {thread.anteriores.length
            ? thread.anteriores.map((r, i) => <Row key={`a-${i}`} reference={r} />)
            : <li className="text-sm text-muted">Sin precedentes.</li>}
        </ul>
      </div>
      <div>
        <p className="mb-2 font-serif text-sm font-semibold text-muted">
          Normas derivadas ({thread.posteriores.length})
        </p>
        <ul className="space-y-1">
          {thread.posteriores.length
            ? thread.posteriores.map((r, i) => <Row key={`p-${i}`} reference={r} />)
            : <li className="text-sm text-muted">Sin normas derivadas.</li>}
        </ul>
      </div>
    </div>
  );
}
