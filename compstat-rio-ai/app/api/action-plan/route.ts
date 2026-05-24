import { NextResponse } from "next/server";
import { buildActionPlan } from "@/lib/actionPlan";

export function GET(): NextResponse {
  return NextResponse.json({ actions: buildActionPlan() });
}
