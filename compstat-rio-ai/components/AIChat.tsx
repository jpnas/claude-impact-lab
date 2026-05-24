"use client";

import React from "react";
import { FormEvent, useState } from "react";
import { Bot, Send, UserRound } from "lucide-react";

type ChatEntry = {
  role: "user" | "assistant";
  content: string;
};

const suggestedQuestions = [
  "Onde a FM deve atuar hoje à noite?",
  "Qual o horário de maior risco?",
  "Quais órgãos precisam agir?",
  "Gere um resumo executivo.",
  "Qual o plano de ação?"
];

export function AIChat(): JSX.Element {
  const [inputValue, setInputValue] = useState(suggestedQuestions[0]);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatEntry[]>([
    {
      role: "assistant",
      content:
        "Diagnóstico\nEstou pronta para cruzar ocorrências, fatores urbanos, inteligência territorial e score de bingo.\n\nEvidências\nOs dados mockados carregam três segmentos críticos do eixo Lauro Müller, General Severiano e Venceslau Brás.\n\nRecomendação operacional\nFaça uma pergunta operacional para gerar orientação de ação.\n\nÓrgãos responsáveis\nForça Municipal, RioLuz, Comlurb, SEOP e SMAS/SMS."
    }
  ]);

  async function submitMessage(message: string): Promise<void> {
    const trimmedMessage = message.trim();

    if (!trimmedMessage) {
      return;
    }

    setIsLoading(true);
    setInputValue("");
    setMessages((currentMessages) => [
      ...currentMessages,
      { role: "user", content: trimmedMessage }
    ]);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmedMessage })
      });
      const payload = (await response.json()) as { answer?: string };

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content: payload.answer ?? "Não foi possível gerar resposta."
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void submitMessage(inputValue);
  }

  return (
    <section className="rounded-lg border border-fuchsia-300/15 bg-rio-panel/80 p-4 shadow-glow">
      <div className="mb-4 flex items-center gap-2">
        <Bot className="h-5 w-5 text-fuchsia-200" aria-hidden="true" />
        <h2 className="text-lg font-semibold text-white">Chat operacional</h2>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {suggestedQuestions.map((question) => (
          <button
            className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-left text-xs text-slate-200 transition hover:border-cyan-300/50 hover:text-cyan-100"
            key={question}
            onClick={() => void submitMessage(question)}
            type="button"
          >
            {question}
          </button>
        ))}
      </div>

      <div className="max-h-[440px] space-y-3 overflow-y-auto pr-1">
        {messages.map((message, messageIndex) => (
          <div
            className={`flex gap-3 rounded-lg border p-3 ${
              message.role === "assistant"
                ? "border-cyan-300/15 bg-cyan-300/5"
                : "border-fuchsia-300/15 bg-fuchsia-300/5"
            }`}
            key={`${message.role}-${messageIndex}`}
          >
            {message.role === "assistant" ? (
              <Bot className="mt-1 h-5 w-5 shrink-0 text-cyan-200" />
            ) : (
              <UserRound className="mt-1 h-5 w-5 shrink-0 text-fuchsia-200" />
            )}
            <p className="whitespace-pre-line text-sm leading-6 text-slate-100">
              {message.content}
            </p>
          </div>
        ))}
      </div>

      <form className="mt-4 flex gap-2" onSubmit={handleSubmit}>
        <input
          aria-label="Pergunta para a IA"
          className="min-w-0 flex-1 rounded-lg border border-white/10 bg-rio-night px-3 py-3 text-sm text-white outline-none ring-cyan-300/40 placeholder:text-slate-500 focus:ring-2"
          onChange={(event) => setInputValue(event.target.value)}
          placeholder="Pergunte sobre atuação, horários, órgãos ou plano..."
          value={inputValue}
        />
        <button
          aria-label="Enviar pergunta"
          className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-cyan-300 text-rio-night transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isLoading}
          type="submit"
        >
          <Send className="h-5 w-5" aria-hidden="true" />
        </button>
      </form>
    </section>
  );
}
