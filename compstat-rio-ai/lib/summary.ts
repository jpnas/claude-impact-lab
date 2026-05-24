import { buildActionPlan } from "./actionPlan";
import { getEnrichedAreaData } from "./mockData";
import { findPrioritySegment } from "./risk";

export type ExecutiveSummary = {
  executiveSummary: string;
  priorityArea: string;
  criticalTime: string;
  bingoIdentified: boolean;
  mainRecommendations: string[];
};

export function buildExecutiveSummary(): ExecutiveSummary {
  const areaData = getEnrichedAreaData();
  const prioritySegment = findPrioritySegment(areaData.segments);
  const bingoSegments = areaData.segments.filter((segment) => segment.bingo);
  const actionPlan = buildActionPlan();
  const readablePeakTime = areaData.peak_time.replace("-", " e ");

  return {
    executiveSummary:
      "O território analisado apresenta convergência entre ocorrências criminais, baixa qualidade urbana, inteligência de rotas de fuga e concentração temporal noturna. A Rua Lauro Müller deve ser tratada como prioridade operacional imediata.",
    priorityArea: prioritySegment.name,
    criticalTime: areaData.peak_time,
    bingoIdentified: bingoSegments.length > 0,
    mainRecommendations: [
      `Reforçar patrulhamento noturno nos trechos críticos entre ${readablePeakTime}.`,
      "Acionar RioLuz e Comlurb para reduzir fatores urbanos que favorecem oportunidade criminal.",
      "Integrar SEOP, SMAS/SMS e Força Municipal em operação territorial coordenada.",
      `Executar primeiro: ${actionPlan[0].action}, sob responsabilidade da ${actionPlan[0].responsible}.`
    ]
  };
}
