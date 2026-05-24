import { describe, expect, it } from "vitest";
import {
  calculateBingo,
  calculateRiskScore,
  classifyRisk,
  enrichSegments
} from "./risk";

describe("risk engine", () => {
  it("sums the four risk layers into the total score", () => {
    const score = calculateRiskScore({
      crime_score: 35,
      urban_factor_score: 30,
      intelligence_score: 25,
      temporal_score: 20
    });

    expect(score).toBe(110);
  });

  it("classifies risk bands according to CompStat Rio rules", () => {
    expect(classifyRisk(18)).toBe("baixo");
    expect(classifyRisk(54)).toBe("médio");
    expect(classifyRisk(88)).toBe("alto");
    expect(classifyRisk(110)).toBe("crítico");
  });

  it("marks bingo when at least three layers are above twenty points", () => {
    const bingo = calculateBingo({
      crime_score: 35,
      urban_factor_score: 30,
      intelligence_score: 25,
      temporal_score: 20
    });

    expect(bingo).toBe(true);
  });

  it("enriches every segment with score, classification, priority and bingo", () => {
    const enrichedSegments = enrichSegments([
      {
        name: "Rua Lauro Müller",
        crime_score: 35,
        urban_factor_score: 30,
        intelligence_score: 25,
        temporal_score: 20
      }
    ]);

    expect(enrichedSegments[0]).toMatchObject({
      totalScore: 110,
      riskLevel: "crítico",
      priority: "Emergencial",
      bingo: true
    });
  });
});
