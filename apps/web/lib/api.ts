// Cliente tipado de la API v1 de AlertaBOE.
// En servidor usa API_BASE (red interna); en cliente, NEXT_PUBLIC_API_BASE.

const SERVER_BASE = process.env.API_BASE ?? "http://127.0.0.1:8000";
const CLIENT_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

function baseUrl(): string {
  return typeof window === "undefined" ? SERVER_BASE : CLIENT_BASE;
}

function headers(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const key = process.env.NEXT_PUBLIC_API_KEY;
  if (key) h["X-API-Key"] = key;
  return h;
}

// ─── Tipos (reflejan boe/core/schemas.py) ────────────────────────────────────

export type Scope = "europeo" | "nacional" | "autonomico" | "otro";

export interface Topic { name: string; slug: string; }
export interface Region { name: string; code: string | null; }
export interface Summary { long: string | null; short: string | null; hook: string | null; }

export interface Document {
  boe_id: string;
  published_at: string;
  title: string;
  seccion: string | null;
  departamento: string | null;
  epigrafe: string | null;
  rango: string | null;
  scope: Scope;
  url_html: string | null;
  url_pdf: string | null;
  consolidated_id: string | null;
  topics: Topic[];
  regions: Region[];
}

export interface DocumentDetail extends Document { summaries: Summary[]; }

export interface Reference {
  rel_type: string;
  direction: "anterior" | "posterior";
  target_boe_id: string | null;
  target_title: string | null;
  raw_text: string | null;
}

export interface Thread {
  boe_id: string;
  title: string;
  anteriores: Reference[];
  posteriores: Reference[];
}

export interface DigestItem {
  boe_id: string;
  title: string;
  departamento: string | null;
  scope: Scope;
  short: string | null;
  url_html: string | null;
}

export interface DigestGroup { scope: Scope; count: number; items: DigestItem[]; }
export interface Digest { fecha: string; total: number; highlights: DigestItem[]; groups: DigestGroup[]; }

export interface SearchHit { document: Document; score: number; matched: string[]; }
export interface SearchResponse { query: string; total: number; results: SearchHit[]; }

export interface Citation { boe_id: string; title: string; url_html: string | null; }
export interface ChatResponse { answer: string; citations: Citation[]; }

export type ContentChannel = "linkedin" | "x" | "tiktok";
export type ContentStatus =
  | "draft" | "approved" | "scheduled" | "published" | "rejected" | "failed";

export interface ContentPost {
  id: number;
  boe_id: string | null;
  channel: ContentChannel;
  status: ContentStatus;
  script: string | null;
  interest_score: number | null;
  asset_path: string | null;
  external_id: string | null;
  published_at: string | null;
  metrics: Record<string, unknown> | null;
}

export interface ContentListResponse { total: number; posts: ContentPost[]; }

// ─── Llamadas ────────────────────────────────────────────────────────────────

async function get<T>(path: string, revalidate = 300): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`, {
    headers: headers(),
    next: { revalidate },
  });
  if (!res.ok) throw new Error(`API ${res.status} en ${path}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status} en ${path}`);
  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, string | undefined>): string {
  const q = Object.entries(params)
    .filter(([, v]) => v)
    .map(([k, v]) => `${k}=${encodeURIComponent(v as string)}`)
    .join("&");
  return q ? `?${q}` : "";
}

export const api = {
  digest: (fecha: string) => get<Digest>(`/v1/digest/${fecha}`),
  document: (boeId: string) => get<DocumentDetail>(`/v1/documents/${boeId}`),
  thread: (boeId: string) => get<Thread>(`/v1/documents/${boeId}/thread`),
  search: (body: Record<string, unknown>) => post<SearchResponse>(`/v1/search`, body),
  chat: (body: Record<string, unknown>) => post<ChatResponse>(`/v1/chat`, body),
  content: (status?: string, channel?: string) =>
    get<ContentListResponse>(`/v1/content${buildQuery({ status, channel })}`, 0),
  approve: (id: number) => post<ContentPost>(`/v1/content/${id}/approve`, {}),
  reject: (id: number) => post<ContentPost>(`/v1/content/${id}/reject`, {}),
  publish: (id: number) => post<ContentPost>(`/v1/content/${id}/publish`, {}),
};

export const SCOPE_LABEL: Record<Scope, string> = {
  europeo: "Europeo",
  nacional: "Nacional",
  autonomico: "Autonómico",
  otro: "Otro",
};
