import React from "react";
import { Activity, Shield } from "lucide-react";
import { AIChat } from "@/components/AIChat";
import { ActionPlanTable } from "@/components/ActionPlanTable";
import { DashboardCards } from "@/components/DashboardCards";
import { RiskMap } from "@/components/RiskMap";
import { buildActionPlan } from "@/lib/actionPlan";
import { getEnrichedAreaData } from "@/lib/mockData";

export default function Home(): React.ReactElement {
  const areaData = getEnrichedAreaData();
  const actionPlan = buildActionPlan();

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.16),transparent_32%),radial-gradient(circle_at_top_right,rgba(139,92,246,0.14),transparent_28%),#050816]">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-white/10 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-medium uppercase tracking-normal text-cyan-100">
              <Shield className="h-4 w-4" aria-hidden="true" />
              CompStat Municipal do Rio
            </div>
            <h1 className="text-3xl font-semibold text-white sm:text-5xl">
              CompStat Rio AI
            </h1>
            <p className="mt-2 max-w-2xl text-base text-slate-300 sm:text-lg">
              Sala de Situação Conversacional para Inteligência Territorial
            </p>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/[0.055] px-4 py-3 text-sm text-slate-200">
            <div className="flex items-center gap-2 text-cyan-100">
              <Activity className="h-4 w-4" aria-hidden="true" />
              Operação sugerida para hoje
            </div>
            <p className="mt-1 text-slate-300">
              {areaData.peak_time} · {areaData.peak_days.join(" e ")}
            </p>
          </div>
        </header>

        <DashboardCards areaData={areaData} />

        <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-6">
            <RiskMap segments={areaData.segments} />
            <ActionPlanTable actions={actionPlan} />
          </div>
          <AIChat />
        </div>
      </div>
    </main>
  );
}
