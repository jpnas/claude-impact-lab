import React from "react";
import { EnrichedAreaSegment, RiskLevel } from "@/lib/risk";

type RiskScoreBadgeProps = {
  segment: Pick<EnrichedAreaSegment, "riskLevel" | "totalScore">;
};

const badgeClassesByRisk: Record<RiskLevel, string> = {
  baixo: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
  médio: "border-cyan-400/40 bg-cyan-400/10 text-cyan-100",
  alto: "border-amber-300/50 bg-amber-300/10 text-amber-100",
  crítico: "border-fuchsia-300/60 bg-fuchsia-400/15 text-fuchsia-100"
};

export function RiskScoreBadge({
  segment
}: RiskScoreBadgeProps): React.ReactElement {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-normal ${badgeClassesByRisk[segment.riskLevel]}`}
    >
      {segment.riskLevel} · {segment.totalScore}
    </span>
  );
}
