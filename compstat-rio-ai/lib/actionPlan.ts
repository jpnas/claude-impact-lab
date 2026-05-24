export type ActionPlanItem = {
  action: string;
  responsible: string;
  priority: "Alta" | "Média";
  justification: string;
  suggestedDeadline: string;
};

export function buildActionPlan(): ActionPlanItem[] {
  return [
    {
      action: "Reforço de patrulhamento noturno",
      responsible: "Força Municipal",
      priority: "Alta",
      justification:
        "Concentração de ocorrências e bingo territorial no intervalo 21h-23h.",
      suggestedDeadline: "Hoje, 19h"
    },
    {
      action: "Poda de vegetação",
      responsible: "Comlurb",
      priority: "Alta",
      justification:
        "Vegetação densa reduz visibilidade e encobre pontos de iluminação.",
      suggestedDeadline: "48 horas"
    },
    {
      action: "Manutenção de iluminação",
      responsible: "RioLuz",
      priority: "Alta",
      justification:
        "Iluminação deficiente amplia oportunidade para roubos a pedestres.",
      suggestedDeadline: "48 horas"
    },
    {
      action: "Ordenamento urbano",
      responsible: "SEOP",
      priority: "Média",
      justification:
        "Obstruções de calçada e comércio irregular aumentam vulnerabilidade.",
      suggestedDeadline: "72 horas"
    },
    {
      action: "Abordagem social",
      responsible: "SMAS/SMS",
      priority: "Média",
      justification:
        "Presença de população vulnerável exige resposta social integrada.",
      suggestedDeadline: "72 horas"
    }
  ];
}
