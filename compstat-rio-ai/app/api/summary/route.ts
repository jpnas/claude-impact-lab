import { NextResponse } from "next/server";
import { buildExecutiveSummary } from "@/lib/summary";

export function GET(): NextResponse {
  return NextResponse.json(buildExecutiveSummary());
}
