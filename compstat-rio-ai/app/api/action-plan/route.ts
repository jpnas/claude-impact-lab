import { NextResponse } from "next/server";
import { getActionPlanFromBackend } from "@/lib/fastApiClient";

export async function GET(): Promise<NextResponse> {
  return NextResponse.json({ actions: await getActionPlanFromBackend() });
}
