import { fetchDimensoes, fetchRelatorio } from "@/lib/api";
import { DimensaoCard } from "@/components/DimensaoCard";
import Link from "next/link";
import { notFound } from "next/navigation";

export const revalidate = 300;

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let dimensoes;
  try {
    dimensoes = await fetchDimensoes(slug);
  } catch {
    notFound();
  }
  const relatorio = await fetchRelatorio(slug);

  const oc = dimensoes.dimensoes.ocorrencias?.dados as Record<string, unknown> | undefined;
  const din = dimensoes.dimensoes.dinamica_criminal?.dados as Record<string, unknown> | undefined;
  const cob = dimensoes.dimensoes.cobertura_operacional?.dados as Record<string, unknown> | undefined;
  const ctx = dimensoes.dimensoes.contexto_territorial?.dados as Record<string, unknown> | undefined;
  const coin = dimensoes.dimensoes.coincidencias?.dados as Record<string, unknown> | undefined;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
          ← Áreas
        </Link>
        <h1 className="text-sm font-bold text-gray-900 flex-1 truncate">
          {dimensoes.area.nome}
        </h1>
        <Link
          href={`/areas/${slug}/relatorio`}
          className="text-sm text-blue-600 hover:underline"
        >
          Gerar Relatório →
        </Link>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Ocorrências */}
        {oc && (
          <DimensaoCard titulo="Ocorrências">
            <p className="text-3xl font-bold text-gray-900">{String(oc.total_periodo ?? 0)}</p>
            <p className="text-sm text-gray-500 mt-1">
              {String(oc.variacao_yoy ?? "N/A")} vs. ano anterior
            </p>
            <p className="text-xs text-gray-400 mt-0.5">{String(oc.periodo_referencia ?? "")}</p>
            <div className="mt-3 space-y-1">
              {Object.entries((oc.por_tipo as Record<string, number>) ?? {})
                .slice(0, 5)
                .map(([tipo, cnt]) => (
                  <div key={tipo} className="flex justify-between text-xs text-gray-600">
                    <span className="truncate mr-2">{tipo}</span>
                    <span className="font-medium flex-shrink-0">{cnt}</span>
                  </div>
                ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Pico: {String(oc.hora_critica ?? "—")} · {String(oc.dia_critico ?? "—")}
            </p>
          </DimensaoCard>
        )}

        {/* Contexto Territorial */}
        {ctx && (
          <DimensaoCard titulo="Contexto Territorial">
            <p className="text-lg font-bold text-red-600">
              {String(ctx.orcrim_dominante ?? "N/A")}
            </p>
            <div className="mt-2 space-y-1">
              {Object.entries((ctx.orcrim_por_tipo as Record<string, number>) ?? {}).map(
                ([org, pct]) => (
                  <div key={org} className="flex justify-between text-xs text-gray-600">
                    <span>{org}</span>
                    <span className="font-medium">{(pct * 100).toFixed(0)}%</span>
                  </div>
                )
              )}
            </div>
            {Boolean(ctx.psr) && (
              <div className="mt-3 text-xs text-gray-500">
                PSR 2024:{" "}
                {String((ctx.psr as Record<string, unknown>)?.total_2024 ?? 0)} ·{" "}
                tendência{" "}
                {String((ctx.psr as Record<string, unknown>)?.tendencia ?? "—")}
              </div>
            )}
          </DimensaoCard>
        )}

        {/* Cobertura Operacional */}
        {cob && (
          <DimensaoCard titulo="Cobertura Operacional">
            <p className="text-2xl font-bold">
              {String(cob.total_cameras ?? 0)}{" "}
              <span className="text-sm font-normal text-gray-500">câmeras</span>
            </p>
            <p className="text-sm text-red-500 mt-1">
              {((cob.pontos_cegos as unknown[]) ?? []).length} pontos cegos
            </p>
            <div className="mt-3 space-y-1">
              {((cob.pontos_cegos as Array<Record<string, unknown>>) ?? [])
                .slice(0, 3)
                .map((pc) => (
                  <div key={String(pc.logradouro)} className="text-xs text-gray-600">
                    {String(pc.logradouro)} ({String(pc.contagem_crimes)} crimes)
                  </div>
                ))}
            </div>
          </DimensaoCard>
        )}

        {/* Dinâmica Criminal */}
        {din && (
          <DimensaoCard titulo="Dinâmica Criminal">
            <p className="text-sm font-semibold text-gray-800">
              {String(din.modalidade_predominante ?? "N/A")}
            </p>
            <p className="text-xs text-gray-500 mt-1 line-clamp-3">
              {String(din.modus_operandi ?? "")}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Suspeitos: {String(din.perfil_suspeitos ?? "—")}
            </p>
          </DimensaoCard>
        )}

        {/* Trechos Críticos */}
        {coin && (
          <div className="md:col-span-2">
            <DimensaoCard titulo="Trechos Críticos">
              <div className="space-y-3">
                {((coin.trechos_criticos as Array<Record<string, unknown>>) ?? [])
                  .slice(0, 5)
                  .map((t) => (
                    <div
                      key={String(t.logradouro)}
                      className="border-l-4 pl-3 border-orange-400"
                    >
                      <div className="flex justify-between items-start">
                        <p className="text-sm font-medium text-gray-800">{String(t.logradouro)}</p>
                        <span className="text-xs font-bold text-orange-600 ml-2">
                          {((t.score_prioridade as number) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{String(t.justificativa ?? "")}</p>
                      {Boolean(t.ponto_cego) && (
                        <span className="text-xs text-red-500">⚠ Ponto cego</span>
                      )}
                    </div>
                  ))}
              </div>
              {Boolean(coin.recomendacoes) && (
                <div className="mt-4 p-3 bg-blue-50 rounded text-xs text-blue-800 space-y-1">
                  <p>
                    <strong>Rota FM:</strong>{" "}
                    {String((coin.recomendacoes as Record<string, unknown>).rota_fm ?? "—")}
                  </p>
                  <p>
                    <strong>Horário:</strong>{" "}
                    {String(
                      (coin.recomendacoes as Record<string, unknown>).horario_patrulhamento ?? "—"
                    )}{" "}
                    · <strong>Modelo:</strong>{" "}
                    {String(
                      (coin.recomendacoes as Record<string, unknown>).modelo_emprego ?? "—"
                    )}
                  </p>
                </div>
              )}
            </DimensaoCard>
          </div>
        )}

        {/* Relatório Salvo */}
        {relatorio && (
          <div className="md:col-span-3">
            <DimensaoCard titulo="Relatório Analítico">
              <div className="max-h-64 overflow-auto">
                <pre className="whitespace-pre-wrap text-xs text-gray-700 font-sans leading-relaxed">
                  {relatorio.conteudo}
                </pre>
              </div>
            </DimensaoCard>
          </div>
        )}
      </div>
    </div>
  );
}
