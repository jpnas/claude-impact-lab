"use client";
import { useState, useRef } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  slug: string;
  relatorioId: string | null;
  onStreamChunk: (text: string) => void;
  onStreamDone: () => void;
  onGerar: () => void;
  streaming: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function RelatorioChatPanel({
  slug,
  relatorioId,
  onStreamChunk,
  onStreamDone,
  onGerar,
  streaming,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [chatStreaming, setChatStreaming] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const sendMessage = async () => {
    if (!input.trim() || !relatorioId || chatStreaming) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatStreaming(true);

    let assistantContent = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    const res = await fetch(`${API_BASE}/areas/${slug}/relatorio/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ relatorio_id: relatorioId, mensagem: userMsg }),
    });
    if (!res.body) { setChatStreaming(false); return; }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") {
          setChatStreaming(false);
          break;
        }
        try {
          const { text } = JSON.parse(payload);
          if (text) {
            assistantContent += text;
            onStreamChunk(text);
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                role: "assistant",
                content: assistantContent,
              };
              return updated;
            });
          }
        } catch {}
      }
    }
    setChatStreaming(false);
  };

  // suppress unused variable warning — onStreamDone is used by parent via prop interface
  void onStreamDone;

  return (
    <div className="flex flex-col h-full border-r bg-gray-50">
      <div className="px-4 py-3 border-b bg-white">
        <h2 className="text-sm font-semibold text-gray-700">Painel de Controle</h2>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-xs text-gray-400 leading-relaxed">
            Gere o relatório e depois refine via chat. As alterações são refletidas no painel direito em tempo real.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-xs p-2.5 rounded-lg ${
              m.role === "user"
                ? "bg-blue-100 text-blue-900 ml-4"
                : "bg-white border text-gray-700 mr-4"
            }`}
          >
            {m.content}
          </div>
        ))}
      </div>
      <div className="p-3 border-t bg-white space-y-2">
        {!relatorioId && (
          <button
            onClick={onGerar}
            disabled={streaming}
            className="w-full py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {streaming ? "Gerando..." : "Gerar Relatório"}
          </button>
        )}
        {relatorioId && (
          <div className="flex gap-2">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ajuste o relatório..."
              className="flex-1 text-sm border rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={chatStreaming}
            />
            <button
              onClick={sendMessage}
              disabled={chatStreaming || !input.trim()}
              className="text-sm px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Enviar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
