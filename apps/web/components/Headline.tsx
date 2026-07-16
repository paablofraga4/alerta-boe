import Link from "next/link";
import type { DigestItem, Document } from "@/lib/api";
import { Kicker } from "./ScopeBadge";

type Item = Pick<Document, "boe_id" | "title" | "departamento" | "scope"> & {
  short?: string | null;
};

// Noticia destacada (portada): titular grande + entradilla.
export function LeadStory({ item }: { item: Item | DigestItem }) {
  const short = "short" in item ? item.short : null;
  return (
    <Link href={`/documento/${item.boe_id}`} className="group block">
      <Kicker scope={item.scope} extra={item.departamento} />
      <h2 className="mt-2 font-serif text-3xl font-semibold leading-[1.1] tracking-tight group-hover:text-crimson sm:text-[2.6rem]">
        {item.title}
      </h2>
      {short && (
        <p className="mt-3 max-w-prose text-[1.05rem] leading-relaxed text-muted">{short}</p>
      )}
      <span className="mt-3 inline-block text-sm font-medium text-crimson">Leer en claro →</span>
    </Link>
  );
}

// Titular de feed: kicker + titular medio + resumen de una o dos líneas.
export function HeadlineItem({ item }: { item: Item | DigestItem }) {
  const short = "short" in item ? item.short : null;
  return (
    <Link href={`/documento/${item.boe_id}`} className="group block border-t border-hair py-5">
      <Kicker scope={item.scope} extra={item.departamento} />
      <h3 className="mt-1.5 font-serif text-xl font-medium leading-snug group-hover:text-crimson">
        {item.title}
      </h3>
      {short && (
        <p className="mt-1.5 line-clamp-2 text-[0.95rem] leading-relaxed text-muted">{short}</p>
      )}
    </Link>
  );
}
