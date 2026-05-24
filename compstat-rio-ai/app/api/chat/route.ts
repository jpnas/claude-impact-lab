import { NextRequest, NextResponse } from "next/server";
import { ChatRequestBody } from "@/lib/chat";
import { getChatFromBackend } from "@/lib/fastApiClient";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = (await request.json()) as Partial<ChatRequestBody>;
  const message = body.message?.trim();

  if (!message) {
    return NextResponse.json(
      { error: "Message is required." },
      { status: 400 }
    );
  }

  const answer = await getChatFromBackend(message);

  return NextResponse.json({ answer });
}
