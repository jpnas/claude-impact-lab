import React from "react";
import { CheckCircle2 } from "lucide-react";
import { ActionPlanItem } from "@/lib/actionPlan";

type ActionPlanTableProps = {
  actions: ActionPlanItem[];
};

export function ActionPlanTable({
  actions
}: ActionPlanTableProps): React.ReactElement {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.055] p-4">
      <div className="mb-4 flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-cyan-300" aria-hidden="true" />
        <h2 className="text-lg font-semibold text-white">Plano de ação</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-separate border-spacing-y-2 text-left text-sm">
          <thead className="text-xs uppercase tracking-normal text-slate-400">
            <tr>
              <th className="px-3 py-2">Ação</th>
              <th className="px-3 py-2">Responsável</th>
              <th className="px-3 py-2">Prioridade</th>
              <th className="px-3 py-2">Justificativa</th>
              <th className="px-3 py-2">Prazo sugerido</th>
            </tr>
          </thead>
          <tbody>
            {actions.map((action) => (
              <tr className="bg-rio-navy/80" key={action.action}>
                <td className="rounded-l-lg px-3 py-3 font-medium text-white">
                  {action.action}
                </td>
                <td className="px-3 py-3 text-cyan-100">
                  {action.responsible}
                </td>
                <td className="px-3 py-3">
                  <span className="rounded-full border border-cyan-300/30 bg-cyan-300/10 px-3 py-1 text-xs font-semibold text-cyan-100">
                    {action.priority}
                  </span>
                </td>
                <td className="px-3 py-3 text-slate-300">
                  {action.justification}
                </td>
                <td className="rounded-r-lg px-3 py-3 text-slate-200">
                  {action.suggestedDeadline}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
