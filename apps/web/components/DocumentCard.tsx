import Link from "next/link";
import type { DigestItem, Document } from "@/lib/api";
import { ScopeBadge } from "./ScopeBadge";

type CardData = Pick<Document, "boe_id" | "title" | "departamento" | "scope"> & {
  short?: string | null;
};

export function DocumentCard({ item }: { item: CardData | DigestItem }) {
  const short = "short" in item ? item.short : null;
  return (
    <Link
      href={`/documento/${item.boe_id}`}
      className="block rounded-lg border border-gray-200 bg-white p-4 transition hover:border-boe-primary hover:shadow-sm dark:border-gray-800 dark:bg-gray-900"
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <ScopeBadge scope={item.scope} />
        <span className="text-xs text-gray-400">{item.boe_id}</span>
      </div>
      <h3 className="font-medium leading-snug">{item.title}</h3>
      {short && <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{short}</p>}
      {item.departamento && (
        <p className="mt-2 text-xs text-gray-400">{item.departamento}</p>
      )}
    </Link>
  );
}
