import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ActionPlanTable } from "./ActionPlanTable";
import { DashboardCards } from "./DashboardCards";
import { RiskMap } from "./RiskMap";
import { buildActionPlan } from "@/lib/actionPlan";
import { getEnrichedAreaData } from "@/lib/mockData";

describe("dashboard components", () => {
  it("renders the main CompStat metrics", () => {
    const areaData = getEnrichedAreaData();

    render(<DashboardCards areaData={areaData} />);

    expect(screen.getByText("Total de ocorrências")).toBeInTheDocument();
    expect(screen.getByText("208")).toBeInTheDocument();
    expect(screen.getByText("Rua Lauro Müller")).toBeInTheDocument();
  });

  it("renders all critical risk areas", () => {
    const areaData = getEnrichedAreaData();

    render(<RiskMap segments={areaData.segments} />);

    expect(screen.getByText("Avenida General Severiano")).toBeInTheDocument();
    expect(screen.getByText("Avenida Venceslau Brás")).toBeInTheDocument();
  });

  it("renders the operational action plan", () => {
    render(<ActionPlanTable actions={buildActionPlan()} />);

    expect(screen.getByText("Manutenção de iluminação")).toBeInTheDocument();
    expect(screen.getByText("RioLuz")).toBeInTheDocument();
  });
});
