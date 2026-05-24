import { NextResponse } from "next/server";
import { getSummaryFromBackend } from "@/lib/fastApiClient";

export async function GET(): Promise<NextResponse> {
  return NextResponse.json(await getSummaryFromBackend());
}
