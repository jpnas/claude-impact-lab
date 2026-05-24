import { ActionPlanItem, buildActionPlan } from "./actionPlan";
import { getEnrichedAreaData, EnrichedMockAreaData } from "./mockData";
import { buildChatResponse } from "./chat";
import { buildExecutiveSummary, ExecutiveSummary } from "./summary";

type ChatPayload = {
  answer: string;
};

type ActionPlanPayload = {
  actions: ActionPlanItem[];
};

function getFastApiBaseUrl(): string {
  return (
    process.env.FASTAPI_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  );
}

async function fetchFromFastApi<ResponseBody>(
  path: string,
  init?: RequestInit
): Promise<ResponseBody> {
  const response = await fetch(`${getFastApiBaseUrl()}${path}`, {
    ...init,
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`FastAPI request failed: ${response.status}`);
  }

  return (await response.json()) as ResponseBody;
}

export async function getAreaFromBackend(): Promise<EnrichedMockAreaData> {
  try {
    return await fetchFromFastApi<EnrichedMockAreaData>("/area");
  } catch {
    return getEnrichedAreaData();
  }
}

export async function getActionPlanFromBackend(): Promise<ActionPlanItem[]> {
  try {
    const payload = await fetchFromFastApi<ActionPlanPayload>("/action-plan");

    return payload.actions;
  } catch {
    return buildActionPlan();
  }
}

export async function getSummaryFromBackend(): Promise<ExecutiveSummary> {
  try {
    return await fetchFromFastApi<ExecutiveSummary>("/summary");
  } catch {
    return buildExecutiveSummary();
  }
}

export async function getChatFromBackend(message: string): Promise<string> {
  try {
    const payload = await fetchFromFastApi<ChatPayload>("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    return payload.answer;
  } catch {
    return buildChatResponse(message);
  }
}
