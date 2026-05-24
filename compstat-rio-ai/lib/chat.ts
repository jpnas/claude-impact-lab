import Anthropic from "@anthropic-ai/sdk";
import { buildActionPlan } from "./actionPlan";
import { buildExecutiveSummary } from "./summary";

export type ChatRequestBody = {
  message: string;
};

function buildPrompt(message: string): string {
  const summary = buildExecutiveSummary();
  const actionPlan = buildActionPlan();

  return `
You are CompStat Rio AI, an operational intelligence assistant for municipal public safety in Rio de Janeiro.
Always answer in Portuguese using exactly these sections:
- Diagnóstico
- Evidências
- Recomendação operacional
- Órgãos responsáveis

Executive context:
${JSON.stringify(summary, null, 2)}

Action plan:
${JSON.stringify(actionPlan, null, 2)}

User question:
${message}
`;
}

export function buildMockChatResponse(message: string): string {
  const normalizedMessage = message.toLowerCase();
  const summary = buildExecutiveSummary();

  if (normalizedMessage.includes("horário")) {
    return `Diagnóstico
O maior risco está concentrado no período ${summary.criticalTime}, com maior exposição em sexta-feira e sábado.

Evidências
Há convergência entre padrão temporal noturno, roubos oportunistas, baixa iluminação e rotas de fuga em áreas de baixa visibilidade.

Recomendação operacional
Antecipar a presença da Força Municipal a partir de 20h30 e manter rondas orientadas por pontos críticos até 23h30.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb e SEOP.`;
  }

  if (normalizedMessage.includes("órgãos") || normalizedMessage.includes("orgaos")) {
    return `Diagnóstico
A resposta precisa combinar presença operacional, correção urbana e assistência social.

Evidências
Os fatores identificados envolvem iluminação, vegetação, comércio irregular, obstrução de calçada e vulnerabilidade social.

Recomendação operacional
Abrir uma operação integrada com responsáveis e prazo por frente de atuação.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS.`;
  }

  if (
    normalizedMessage.includes("plano") ||
    normalizedMessage.includes("ação") ||
    normalizedMessage.includes("atuar")
  ) {
    return `Diagnóstico
A prioridade operacional de hoje é a ${summary.priorityArea}, pois apresenta bingo territorial e score crítico.

Evidências
O trecho combina crime, fatores urbanos, inteligência territorial e concentração no horário ${summary.criticalTime}.

Recomendação operacional
Reforçar patrulhamento noturno, corrigir iluminação, podar vegetação e ordenar calçadas em ação coordenada.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS.`;
  }

  return `Diagnóstico
O território analisado exige resposta integrada porque há convergência de risco criminal, urbano, temporal e territorial.

Evidências
Foram registradas 208 ocorrências no período 2023-2024, com pico entre ${summary.criticalTime} e bingo identificado em área prioritária.

Recomendação operacional
Executar operação noturna na ${summary.priorityArea}, combinando presença ostensiva e correções urbanas rápidas.

Órgãos responsáveis
Força Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS.`;
}

export async function buildChatResponse(message: string): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    return buildMockChatResponse(message);
  }

  const anthropic = new Anthropic({ apiKey });
  const response = await anthropic.messages.create({
    model: "claude-3-5-sonnet-latest",
    max_tokens: 700,
    messages: [
      {
        role: "user",
        content: buildPrompt(message)
      }
    ]
  });

  const textBlocks = response.content
    .filter((contentBlock) => contentBlock.type === "text")
    .map((contentBlock) => contentBlock.text);

  return textBlocks.join("\n\n");
}
