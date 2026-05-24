export type RiskLevel = "baixo" | "médio" | "alto" | "crítico";
export type PriorityLevel = "Baixa" | "Média" | "Alta" | "Emergencial";

export type RiskLayerScores = {
  crime_score: number;
  urban_factor_score: number;
  intelligence_score: number;
  temporal_score: number;
};

export type AreaSegment = RiskLayerScores & {
  name: string;
};

export type EnrichedAreaSegment = AreaSegment & {
  totalScore: number;
  riskLevel: RiskLevel;
  priority: PriorityLevel;
  bingo: boolean;
};

export function calculateRiskScore(segment: RiskLayerScores): number {
  return (
    segment.crime_score +
    segment.urban_factor_score +
    segment.intelligence_score +
    segment.temporal_score
  );
}

export function classifyRisk(totalScore: number): RiskLevel {
  if (totalScore > 100) {
    return "crítico";
  }

  if (totalScore >= 70) {
    return "alto";
  }

  if (totalScore >= 40) {
    return "médio";
  }

  return "baixo";
}

export function calculateBingo(segment: RiskLayerScores): boolean {
  const elevatedLayers = [
    segment.crime_score,
    segment.urban_factor_score,
    segment.intelligence_score,
    segment.temporal_score
  ].filter((layerScore) => layerScore > 20);

  return elevatedLayers.length >= 3;
}

export function priorityFromRisk(riskLevel: RiskLevel): PriorityLevel {
  const priorityByRisk: Record<RiskLevel, PriorityLevel> = {
    baixo: "Baixa",
    médio: "Média",
    alto: "Alta",
    crítico: "Emergencial"
  };

  return priorityByRisk[riskLevel];
}

export function enrichSegments(segments: AreaSegment[]): EnrichedAreaSegment[] {
  return segments.map((segment) => {
    const totalScore = calculateRiskScore(segment);
    const riskLevel = classifyRisk(totalScore);

    return {
      ...segment,
      totalScore,
      riskLevel,
      priority: priorityFromRisk(riskLevel),
      bingo: calculateBingo(segment)
    };
  });
}

export function findPrioritySegment(
  segments: EnrichedAreaSegment[]
): EnrichedAreaSegment {
  return [...segments].sort(
    (firstSegment, secondSegment) =>
      secondSegment.totalScore - firstSegment.totalScore
  )[0];
}
