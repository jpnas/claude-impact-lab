import React from "react";
import { Route, ShieldAlert } from "lucide-react";
import { EnrichedAreaSegment } from "@/lib/risk";
import { RiskScoreBadge } from "./RiskScoreBadge";

type RiskMapProps = {
  segments: EnrichedAreaSegment[];
};

export function RiskMap({ segments }: RiskMapProps): React.ReactElement {
  return (
    <section className="rounded-lg border border-cyan-300/15 bg-rio-panel/70 p-4 shadow-glow">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Visualização territorial de risco
          </h2>
          <p className="text-sm text-slate-300">
            Trechos críticos priorizados por score e bingo operacional.
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-cyan-200">
          <Route className="h-4 w-4" aria-hidden="true" />
          Botafogo · Urca · Eixo de circulação
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-3">
        {segments.map((segment, segmentIndex) => (
          <article
            className="relative overflow-hidden rounded-lg border border-white/10 bg-rio-navy p-4"
            key={segment.name}
          >
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan-300 via-fuchsia-400 to-violet-500" />
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-normal text-slate-400">
                  Área {segmentIndex + 1}
                </p>
                <h3 className="mt-1 text-base font-semibold text-white">
                  {segment.name}
                </h3>
              </div>
              {segment.bingo ? (
                <ShieldAlert className="h-5 w-5 text-fuchsia-300" />
              ) : null}
            </div>

            <div className="mt-4">
              <RiskScoreBadge segment={segment} />
            </div>

            <div className="mt-5 space-y-2 text-sm text-slate-300">
              <div className="flex justify-between">
                <span>Crime</span>
                <span>{segment.crime_score}</span>
              </div>
              <div className="flex justify-between">
                <span>Fator urbano</span>
                <span>{segment.urban_factor_score}</span>
              </div>
              <div className="flex justify-between">
                <span>Inteligência</span>
                <span>{segment.intelligence_score}</span>
              </div>
              <div className="flex justify-between">
                <span>Temporal</span>
                <span>{segment.temporal_score}</span>
              </div>
            </div>

            <div className="mt-4 h-2 rounded-full bg-white/10">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-cyan-300 to-fuchsia-400"
                style={{ width: `${Math.min(segment.totalScore, 120) / 1.2}%` }}
              />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
