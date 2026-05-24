"use client";
import ReactMarkdown from "react-markdown";

interface Props {
  conteudo: string;
  streaming: boolean;
  onSalvar: () => void;
}

export function RelatorioArtifact({ conteudo, streaming, onSalvar }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b bg-white">
        <span className="text-sm font-medium text-gray-700 flex items-center gap-2">
          Relatório Analítico
          {streaming && (
            <span className="inline-block w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          )}
        </span>
        {!streaming && conteudo && (
          <button
            onClick={onSalvar}
            className="text-xs px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
          >
            Salvar Relatório
          </button>
        )}
      </div>
      <div className="flex-1 overflow-auto p-6 prose prose-sm max-w-none">
        {conteudo ? (
          <ReactMarkdown>{conteudo}</ReactMarkdown>
        ) : (
          <p className="text-gray-400 text-sm">
            Clique em &quot;Gerar Relatório&quot; para começar.
          </p>
        )}
      </div>
    </div>
  );
}
