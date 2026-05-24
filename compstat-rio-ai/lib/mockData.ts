import mockArea from "@/data/mock-area.json";
import { AreaSegment, enrichSegments, EnrichedAreaSegment } from "./risk";

export type UrbanFactor = {
  factor: string;
  responsible: string;
  priority: "Alta" | "Média" | "Baixa";
};

export type TerritorialIntelligence = {
  modus_operandi: string;
  escape_routes: string[];
  receptation_points: string[];
};

export type MockAreaData = {
  area: string;
  period: string;
  total_occurrences: number;
  critical_segments: number;
  peak_time: string;
  peak_days: string[];
  crime_patterns: string[];
  urban_factors: UrbanFactor[];
  intelligence: TerritorialIntelligence;
  segments: AreaSegment[];
};

export type EnrichedMockAreaData = Omit<MockAreaData, "segments"> & {
  segments: EnrichedAreaSegment[];
};

export function getMockAreaData(): MockAreaData {
  return mockArea as MockAreaData;
}

export function getEnrichedAreaData(): EnrichedMockAreaData {
  const areaData = getMockAreaData();

  return {
    ...areaData,
    segments: enrichSegments(areaData.segments)
  };
}
