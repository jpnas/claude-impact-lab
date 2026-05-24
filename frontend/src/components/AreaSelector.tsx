"use client";
import { Area } from "@/lib/api";
import Link from "next/link";

export function AreaSelector({ areas }: { areas: Area[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
      {areas.map((area) => (
        <div
          key={area.slug}
          className={`rounded-lg border p-5 transition-colors ${
            area.cache_disponivel
              ? "border-blue-400 bg-blue-50 hover:bg-blue-100"
              : "border-gray-200 bg-gray-50 opacity-60"
          }`}
        >
          <h2 className="font-semibold text-gray-900 text-sm mb-3 leading-snug">{area.nome}</h2>
          <div className="flex gap-2">
            {area.cache_disponivel ? (
              <>
                <Link
                  href={`/areas/${area.slug}/relatorio`}
                  className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Gerar Relatório
                </Link>
                <Link
                  href={`/areas/${area.slug}/dashboard`}
                  className="text-xs px-3 py-1.5 border border-blue-600 text-blue-600 rounded hover:bg-blue-50 transition-colors"
                >
                  Dashboard
                </Link>
              </>
            ) : (
              <span className="text-xs text-gray-400">Pipeline não executado</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
