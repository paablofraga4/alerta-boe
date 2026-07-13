"use client";

import type { ContentPost } from "@/lib/api";

const CHANNEL_LABEL: Record<string, string> = {
  linkedin: "in LinkedIn",
  x: "𝕏",
  tiktok: "TikTok",
};

const STATUS_STYLE: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  approved: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200",
  published: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200",
  rejected: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200",
  failed: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200",
  scheduled: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
};

interface Props {
  post: ContentPost;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
  onPublish: () => void;
}

export function ContentCard({ post, busy, onApprove, onReject, onPublish }: Props) {
  const validation =
    (post.metrics?.validation as { ok?: boolean; issues?: string[] } | undefined) ?? undefined;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded bg-boe-accent/10 px-2 py-0.5 text-xs font-medium text-boe-accent">
            {CHANNEL_LABEL[post.channel] ?? post.channel}
          </span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[post.status] ?? ""}`}>
            {post.status}
          </span>
          {typeof post.interest_score === "number" && (
            <span className="text-xs text-gray-400">interés {post.interest_score.toFixed(2)}</span>
          )}
        </div>
        {post.boe_id && <span className="text-xs text-gray-400">{post.boe_id}</span>}
      </div>

      <p className="whitespace-pre-wrap text-sm text-gray-700 dark:text-gray-300">
        {post.script}
      </p>

      {validation && (
        <p className="mt-2 text-xs">
          {validation.ok ? (
            <span className="text-green-600">✓ Validado</span>
          ) : (
            <span className="text-amber-600">
              ⚠ Revisar{validation.issues?.length ? `: ${validation.issues.join("; ")}` : ""}
            </span>
          )}
        </p>
      )}

      <div className="mt-3 flex gap-2">
        {post.status === "draft" && (
          <>
            <button
              onClick={onApprove}
              disabled={busy}
              className="rounded bg-boe-accent px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
            >
              Aprobar
            </button>
            <button
              onClick={onReject}
              disabled={busy}
              className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50 dark:border-gray-700"
            >
              Rechazar
            </button>
          </>
        )}
        {post.status === "approved" && (
          <button
            onClick={onPublish}
            disabled={busy}
            className="rounded bg-boe-primary px-3 py-1 text-sm font-medium text-white disabled:opacity-50"
          >
            Publicar
          </button>
        )}
        {post.status === "published" && post.external_id && (
          <span className="text-xs text-gray-400">Publicado · {post.external_id}</span>
        )}
      </div>
    </div>
  );
}
