import { SCOPE_LABEL, type Scope } from "@/lib/api";

// Kicker editorial (versalitas) con el ámbito y, opcionalmente, el departamento.
export function Kicker({ scope, extra }: { scope: Scope; extra?: string | null }) {
  return (
    <p className="kicker">
      {SCOPE_LABEL[scope]}
      {extra ? <span className="text-muted"> · {extra}</span> : null}
    </p>
  );
}

export function ScopeBadge({ scope }: { scope: Scope }) {
  return (
    <span className="rounded-sm border border-hair px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide text-muted">
      {SCOPE_LABEL[scope]}
    </span>
  );
}
