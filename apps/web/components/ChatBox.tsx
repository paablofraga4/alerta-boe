"use client";

import { useState } from "react";
import { api, type Citation } from "@/lib/api";

interface Turn {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
}

export function ChatBox({ boeId }: { boeId: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question) return;
    setTurns((t) => [...t, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    try {
      // El chat recupera contexto de todo el corpus; sugerimos el boe_id en la consulta.
      const res = await api.chat({ message: `${question} (contexto: ${boeId})` });
      setTurns((t) => [
        ...t,
        { role: "assistant", text: res.answer, citations: res.citations },
      ]);
    } catch {
      setTurns((t) => [
        ...t,
        { role: "assistant", text: "El asistente no está disponible ahora mismo." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-800">
      <div className="max-h-80 space-y-3 overflow-y-auto p-4">
        {turns.length === 0 && (
          <p className="text-sm text-gray-400">
            Pregunta lo que quieras sobre esta publicación. El asistente responde
            citando el BOE.
          </p>
        )}
        {turns.map((turn, i) => (
          <div
            key={i}
            className={turn.role === "user" ? "text-right" : "text-left"}
          >
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                turn.role === "user"
                  ? "bg-boe-accent text-white"
                  : "bg-gray-100 dark:bg-gray-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{turn.text}</p>
              {turn.citations && turn.citations.length > 0 && (
                <ul className="mt-2 space-y-0.5 border-t border-gray-300/40 pt-2 text-xs">
                  {turn.citations.map((c) => (
                    <li key={c.boe_id}>
                      <a
                        href={`/documento/${c.boe_id}`}
                        className="underline decoration-dotted"
                      >
                        [{c.boe_id}] {c.title}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-gray-400">Pensando…</p>}
      </div>
      <form onSubmit={send} className="flex gap-2 border-t border-gray-200 p-3 dark:border-gray-800">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="¿Cómo me afecta?"
          className="flex-1 rounded border border-gray-300 bg-transparent px-3 py-1.5 text-sm dark:border-gray-700"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-boe-primary px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
