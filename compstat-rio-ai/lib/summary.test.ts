import { describe, expect, it } from "vitest";
import { buildActionPlan } from "./actionPlan";
import { buildMockChatResponse } from "./chat";
import { buildExecutiveSummary } from "./summary";

describe("CompStat API helpers", () => {
  it("builds an executive summary with priority area and bingo status", () => {
    const summary = buildExecutiveSummary();

    expect(summary.priorityArea).toBe("Rua Lauro Müller");
    expect(summary.criticalTime).toBe("21h-23h");
    expect(summary.bingoIdentified).toBe(true);
    expect(summary.mainRecommendations).toContain(
      "Reforçar patrulhamento noturno nos trechos críticos entre 21h e 23h."
    );
  });

  it("builds an operational action plan with responsible agencies", () => {
    const actionPlan = buildActionPlan();

    expect(actionPlan).toHaveLength(5);
    expect(actionPlan[0]).toMatchObject({
      action: "Reforço de patrulhamento noturno",
      responsible: "Força Municipal",
      priority: "Alta"
    });
  });

  it("returns a structured mock AI answer when no Claude key is available", () => {
    const answer = buildMockChatResponse("Qual o plano de ação?");

    expect(answer).toContain("Diagnóstico");
    expect(answer).toContain("Evidências");
    expect(answer).toContain("Recomendação operacional");
    expect(answer).toContain("Órgãos responsáveis");
  });
});
