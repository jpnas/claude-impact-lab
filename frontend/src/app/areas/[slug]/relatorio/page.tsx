"use client";
import { use, useState, useCallback } from "react";
import { RelatorioChatPanel } from "@/components/RelatorioChatPanel";
import { RelatorioArtifact } from "@/components/RelatorioArtifact";
import { salvarRelatorio } from "@/lib/api";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function RelatorioPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [conteudo, setConteudo] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [relatorioId, setRelatorioId] = useState<string | null>(null);

  const handleGerar = useCallback(async () => {
    setConteudo("");
    setStreaming(true);
    try {
      const res = await fetch(`${API_BASE}/areas/${slug}/relatorio/gerar`, {
        method: "POST",
      });
      if (!res.body) { setStreaming(false); return; }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value).split("\n");
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          if (payload === "[DONE]") { setStreaming(false); break; }
          try {
            const { text } = JSON.parse(payload);
            if (text) setConteudo((c) => c + text);
          } catch {}
        }
      }
    } catch {
      setStreaming(false);
    }
  }, [slug]);

  const handleSalvar = useCallback(async () => {
    try {
      const saved = await salvarRelatorio(slug, conteudo);
      setRelatorioId(saved.id);
      alert("Relatório salvo com sucesso!");
    } catch {
      alert("Erro ao salvar relatório.");
    }
  }, [slug, conteudo]);

  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="flex items-center gap-4 px-4 py-2 border-b bg-white">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
          ← Áreas
        </Link>
        <h1 className="text-sm font-semibold text-gray-900 flex-1 truncate">
          {slug} — Relatório Analítico
        </h1>
        <Link
          href={`/areas/${slug}/dashboard`}
          className="text-sm text-blue-600 hover:underline"
        >
          Ver Dashboard →
        </Link>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-72 flex-shrink-0 overflow-hidden">
          <RelatorioChatPanel
            slug={slug}
            relatorioId={relatorioId}
            onStreamChunk={(t) => setConteudo((c) => c + t)}
            onStreamDone={() => setStreaming(false)}
            onGerar={handleGerar}
            streaming={streaming}
          />
        </div>
        <div className="flex-1 overflow-hidden">
          <RelatorioArtifact
            conteudo={conteudo}
            streaming={streaming}
            onSalvar={handleSalvar}
          />
        </div>
      </div>
    </div>
  );
}
