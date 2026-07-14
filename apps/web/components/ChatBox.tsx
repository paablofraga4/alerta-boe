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
      const res = await api.chat({ message: `${question} (contexto: ${boeId})` });
      setTurns((t) => [...t, { role: "assistant", text: res.answer, citations: res.citations }]);
    } catch {
      setTurns((t) => [...t, { role: "assistant", text: "El asistente no está disponible ahora mismo." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-sm border border-hair bg-card">
      <div className="max-h-80 space-y-3 overflow-y-auto p-4">
        {turns.length === 0 && (
          <p className="text-sm text-muted">Pregunta lo que quieras sobre esta publicación.</p>
        )}
        {turns.map((turn, i) => (
          <div key={i} className={turn.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                turn.role === "user" ? "bg-crimson text-white" : "bg-paper"
              }`}
            >
              <p className="whitespace-pre-wrap">{turn.text}</p>
              {turn.citations && turn.citations.length > 0 && (
                <ul className="mt-2 space-y-0.5 border-t border-hair pt-2 text-xs">
                  {turn.citations.map((c) => (
                    <li key={c.boe_id}>
                      <a href={`/documento/${c.boe_id}`} className="underline decoration-dotted">
                        [{c.boe_id}] {c.title}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-muted">Pensando…</p>}
      </div>
      <form onSubmit={send} className="flex gap-2 border-t border-hair p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="¿Cómo me afecta?"
          className="flex-1 rounded-sm border border-hair bg-transparent px-3 py-1.5 text-sm"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-sm bg-crimson px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
    </div>
  );
}
