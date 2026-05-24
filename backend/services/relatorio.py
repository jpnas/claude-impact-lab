from __future__ import annotations
import anthropic
import os
import json
from backend.db import get_db
from backend.services.dimensoes import get_dimensoes


def _build_system_prompt(dimensoes: dict) -> str:
    area = dimensoes["area"]["nome"]
    dims = dimensoes["dimensoes"]

    def _fmt(tipo: str, max_chars: int) -> str:
        d = dims.get(tipo, {}).get("dados", {})
        return json.dumps(d, ensure_ascii=False)[:max_chars]

    return f"""Você é um analista de segurança pública do CompStat Municipal do Rio de Janeiro.
Você tem acesso às seguintes dimensões de análise da área FM "{area}":

**Ocorrências:** {_fmt('ocorrencias', 3000)}
**Dinâmica Criminal:** {_fmt('dinamica_criminal', 2000)}
**Fatores Urbanos:** {_fmt('fatores_urbanos', 1500)}
**Cobertura Operacional:** {_fmt('cobertura_operacional', 1500)}
**Contexto Territorial:** {_fmt('contexto_territorial', 1000)}
**Coincidências e Recomendações:** {_fmt('coincidencias', 2000)}

Gere relatórios analíticos objetivos, em português, para subsidiar decisões operacionais na reunião semanal do CompStat presidida pelo Prefeito."""


RELATORIO_PROMPT = """Gere o Relatório Analítico de Área completo. Estruture em seções:
1. Resumo Executivo (3-4 frases)
2. Análise de Ocorrências (volume, tendência, distribuição temporal, logradouros críticos)
3. Dinâmica Criminal (modalidade, modus operandi, ORCRIM)
4. Fatores Urbanos e Cobertura
5. Trechos Críticos e Score de Prioridade
6. Recomendações Operacionais (rota FM, horário, modelo de emprego)
7. Ações Municipais Propostas (por órgão)

Use linguagem técnica e objetiva. Formato markdown."""


async def stream_relatorio(slug: str):
    dimensoes = get_dimensoes(slug)
    if not dimensoes:
        yield f"data: {json.dumps({'error': 'Área não encontrada'})}\n\n"
        return

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system = _build_system_prompt(dimensoes)

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": RELATORIO_PROMPT}],
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'text': text})}\n\n"
    yield "data: [DONE]\n\n"


async def stream_chat(slug: str, relatorio_id: str, user_message: str):
    db = get_db()
    dimensoes = get_dimensoes(slug)

    msgs_res = (
        db.table("mensagens_relatorio")
        .select("role,conteudo")
        .eq("relatorio_id", relatorio_id)
        .order("criado_em")
        .execute()
    )
    history = [{"role": m["role"], "content": m["conteudo"]} for m in msgs_res.data]
    history.append({"role": "user", "content": user_message})

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system = _build_system_prompt(dimensoes) if dimensoes else "Analista CompStat Rio."

    full_response = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=history,
    ) as stream:
        for text in stream.text_stream:
            full_response += text
            yield f"data: {json.dumps({'text': text})}\n\n"

    db.table("mensagens_relatorio").insert(
        {"relatorio_id": relatorio_id, "role": "user", "conteudo": user_message}
    ).execute()
    db.table("mensagens_relatorio").insert(
        {"relatorio_id": relatorio_id, "role": "assistant", "conteudo": full_response}
    ).execute()
    yield "data: [DONE]\n\n"
