import React from "react";
import {
  AlertTriangle,
  BadgeCheck,
  Clock3,
  Crosshair,
  MapPinned
} from "lucide-react";
import { EnrichedMockAreaData } from "@/lib/mockData";
import { findPrioritySegment } from "@/lib/risk";
import { RiskScoreBadge } from "./RiskScoreBadge";

type DashboardCardsProps = {
  areaData: EnrichedMockAreaData;
};

export function DashboardCards({
  areaData
}: DashboardCardsProps): React.ReactElement {
  const prioritySegment = findPrioritySegment(areaData.segments);
  const bingoCount = areaData.segments.filter((segment) => segment.bingo).length;

  const cards = [
    {
      label: "Total de ocorrências",
      value: areaData.total_occurrences.toString(),
      detail: areaData.period,
      icon: AlertTriangle
    },
    {
      label: "Área mais crítica",
      value: prioritySegment.name,
      detail: prioritySegment.priority,
      icon: MapPinned
    },
    {
      label: "Horário de pico",
      value: areaData.peak_time,
      detail: areaData.peak_days.join(" e "),
      icon: Clock3
    },
    {
      label: "Score de risco",
      value: prioritySegment.totalScore.toString(),
      detail: prioritySegment.riskLevel,
      icon: Crosshair
    },
    {
      label: "Bingos identificados",
      value: bingoCount.toString(),
      detail: "camadas convergentes",
      icon: BadgeCheck
    }
  ];

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => {
        const Icon = card.icon;

        return (
          <article
            className="rounded-lg border border-white/10 bg-white/[0.055] p-4 shadow-glow"
            key={card.label}
          >
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-medium uppercase tracking-normal text-cyan-100/70">
                {card.label}
              </p>
              <Icon className="h-5 w-5 text-cyan-300" aria-hidden="true" />
            </div>
            <div className="mt-4 min-h-16">
              <p className="break-words text-2xl font-semibold text-white">
                {card.value}
              </p>
              <p className="mt-1 text-sm text-slate-300">{card.detail}</p>
            </div>
          </article>
        );
      })}
      <div className="hidden">
        <RiskScoreBadge segment={prioritySegment} />
      </div>
    </section>
  );
}
