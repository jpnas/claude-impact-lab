import { NextRequest, NextResponse } from "next/server";
import { buildChatResponse, ChatRequestBody } from "@/lib/chat";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = (await request.json()) as Partial<ChatRequestBody>;
  const message = body.message?.trim();

  if (!message) {
    return NextResponse.json(
      { error: "Message is required." },
      { status: 400 }
    );
  }

  const answer = await buildChatResponse(message);

  return NextResponse.json({ answer });
}
