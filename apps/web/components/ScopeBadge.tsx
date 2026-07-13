import { SCOPE_LABEL, type Scope } from "@/lib/api";

const STYLES: Record<Scope, string> = {
  nacional: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200",
  europeo: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200",
  autonomico: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200",
  otro: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

export function ScopeBadge({ scope }: { scope: Scope }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[scope]}`}>
      {SCOPE_LABEL[scope]}
    </span>
  );
}
