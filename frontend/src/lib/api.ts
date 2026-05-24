const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Area {
  id: string;
  nome: string;
  slug: string;
  cache_disponivel: boolean;
}

export interface Dimensoes {
  area: Area;
  dimensoes: Record<string, { dados: unknown; referencia_pipeline: string }>;
}

export async function fetchAreas(): Promise<Area[]> {
  const res = await fetch(`${API_BASE}/areas`);
  if (!res.ok) throw new Error("Erro ao buscar áreas");
  return res.json();
}

export async function fetchDimensoes(slug: string): Promise<Dimensoes> {
  const res = await fetch(`${API_BASE}/areas/${slug}/dimensoes`);
  if (!res.ok) throw new Error("Área não encontrada");
  return res.json();
}

export async function fetchRelatorio(slug: string, reuniaoId?: string) {
  const url = reuniaoId
    ? `${API_BASE}/areas/${slug}/relatorio?reuniao_id=${reuniaoId}`
    : `${API_BASE}/areas/${slug}/relatorio`;
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Erro ao buscar relatório");
  return res.json();
}

export async function salvarRelatorio(slug: string, conteudo: string, reuniaoId?: string) {
  const res = await fetch(`${API_BASE}/areas/${slug}/relatorio`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conteudo, reuniao_id: reuniaoId, status: "finalizado" }),
  });
  if (!res.ok) throw new Error("Erro ao salvar relatório");
  return res.json();
}

export function streamRelatorio(
  slug: string,
  onChunk: (text: string) => void,
  onDone: () => void,
): () => void {
  const controller = new AbortController();
  fetch(`${API_BASE}/areas/${slug}/relatorio/gerar`, {
    method: "POST",
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.body) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") { onDone(); return; }
        try {
          const { text } = JSON.parse(payload);
          if (text) onChunk(text);
        } catch {}
      }
    }
  }).catch(() => {});
  return () => controller.abort();
}

export function streamChat(
  slug: string,
  relatorioId: string,
  mensagem: string,
  onChunk: (text: string) => void,
  onDone: () => void,
): () => void {
  const controller = new AbortController();
  fetch(`${API_BASE}/areas/${slug}/relatorio/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ relatorio_id: relatorioId, mensagem }),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.body) return;
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") { onDone(); return; }
        try {
          const { text } = JSON.parse(payload);
          if (text) onChunk(text);
        } catch {}
      }
    }
  }).catch(() => {});
  return () => controller.abort();
}
