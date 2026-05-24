from __future__ import annotations
import anthropic
import os
import json
import uuid
from backend.db import get_db
from backend.services.dimensoes import get_dimensoes


# Chaves com arrays de coordenadas que só pesam no contexto e não entram no
# relatório textual — removidas antes de enviar ao modelo (mantém-se a contagem).
_CHAVES_PESADAS = {
    "heatmap_points", "pontos", "coordinates", "poligono", "cameras", "pontos_cegos",
}


def _compactar(obj):
    """Remove arrays de coordenadas, preservando a contagem (`<chave>_qtd`)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in _CHAVES_PESADAS:
                if isinstance(v, list):
                    out[f"{k}_qtd"] = len(v)
            else:
                out[k] = _compactar(v)
        return out
    if isinstance(obj, list):
        return [_compactar(x) for x in obj]
    return obj


def _build_system_prompt(dimensoes: dict) -> str:
    area = dimensoes["area"]["nome"]
    dims = dimensoes["dimensoes"]

    def _fmt(tipo: str) -> str:
        d = dims.get(tipo, {}).get("dados", {})
        return json.dumps(_compactar(d), ensure_ascii=False)

    return f"""Você é um analista de segurança pública do CompStat Municipal do Rio de Janeiro.
Você produz o Relatório Analítico de Área para a reunião semanal do CompStat presidida pelo Prefeito.

Dimensões de análise da área FM "{area}" (JSON):

**Ocorrências:** {_fmt('ocorrencias')}
**Dinâmica Criminal:** {_fmt('dinamica_criminal')}
**Fatores Urbanos:** {_fmt('fatores_urbanos')}
**Cobertura Operacional:** {_fmt('cobertura_operacional')}
**Contexto Territorial:** {_fmt('contexto_territorial')}
**Coincidências e Recomendações:** {_fmt('coincidencias')}

REGRAS DE INTEGRIDADE (obrigatórias):
- Use SOMENTE os dados acima. Nunca invente números, endereços, órgãos ou estatísticas.
- Campos sem dado disponível devem ser preenchidos com o marcador literal `_[Pendente — registros da FM-Rio]_`. NÃO estime.
- Se a Dinâmica Criminal estiver marcada como indisponível, declare isso explicitamente em vez de descrever um modus operandi.
- Língua: português. Tom técnico e objetivo. Saída em markdown."""


RELATORIO_PROMPT = """Gere o **Relatório Analítico de Área** seguindo EXATAMENTE o template oficial da Secretaria-geral do CompStat Municipal abaixo. Use tabelas markdown. Não acrescente nem remova seções.

# RELATÓRIO ANALÍTICO DE ÁREA
### Subsídio para Reunião de CompStat

| Área de análise | Período de análise |
|---|---|
| {nome da área} | **Dados criminais:** {periodo_referencia das ocorrências} |

## Resumo Executivo

3 a 4 frases sintetizando volume de crime, padrão temporal predominante, principais fatores urbanos e a recomendação central.

## Perguntas Norteadoras

| Pergunta norteadora | Diagnóstico com base nos dados | Operação FM / órgãos complementares | Observação / sugestão de ajuste (COMPSTAT) |
|---|---|---|---|
| Locais de maior incidência criminal estão coincidindo com a rota da FM? | (cite os trechos críticos de maior score e se são ponto cego) | (sugestão de rota) | - |
| Horário de maior incidência criminal está coincidindo com QMD? | (use hora_critica e dia_critico) | (sugestão de horário) | - |
| Dinâmica criminal coincide com o modelo de emprego da FM? | (modalidade / ORCRIM, ou "indisponível") | (modelo de emprego: a pé / moto / viatura) | - |
| Fatores relevantes para o crime estão sendo resolvidos pelos órgãos complementares? | (UMA LINHA por fator relevante) | (órgão responsável + ação) | - |

## 1. Ocorrências Criminais

### Identificação da Área
| Campo | Valor |
|---|---|
| Área FM | {nome} |
| Número de trechos críticos | {qtd de trechos_criticos} |
| AISP | _[Pendente — registros da FM-Rio]_ |
| Base FM | _[Pendente — registros da FM-Rio]_ |
| Bairro | _[Pendente — registros da FM-Rio]_ |
| Subprefeitura | _[Pendente — registros da FM-Rio]_ |
| DP | _[Pendente — registros da FM-Rio]_ |
| BPM | _[Pendente — registros da FM-Rio]_ |
| Área sob influência de grupo criminoso | {orcrim_dominante do contexto territorial} |

### Indicadores do Período
| Período | Roubos | Furtos | Total | Ranking | Variação s/ período anterior |
|---|---|---|---|---|---|
| {periodo_referencia} | {total_periodo} | N/A | {total_periodo} | _[Pendente]_ | {variacao_yoy} |

### Distribuição de Ocorrências por Tipo
Tabela com Ranking, Tipo de ocorrência e Qtd no período (a partir de `por_tipo`, em ordem decrescente).

### Análise Temporal
- **Dia / horário crítico:** {dia_critico}, {hora_critica}.
- **Período predominante:** descreva a concentração a partir de `por_hora` e `por_dia_semana`.

## 2. Dinâmica Criminal

| Campo | Conteúdo |
|---|---|
| Dinâmica do crime | {narrativa_completa / modus_operandi, ou "Análise indisponível para esta área"} |
| Modalidade | {modalidade_predominante} |
| Áreas de fuga e escoamento de bens | {rotas_de_fuga e pontos_de_receptacao, ou "Não disponível"} |

## 3. Efetivo Empregado – Força Municipal

| Campo | Situação atual | Sugestão de alteração | Justificativa |
|---|---|---|---|
| Nº de Agentes por Turno | _[Pendente — registros da FM-Rio]_ | - | - |
| Locais de Cobertura | _[Pendente — registros da FM-Rio]_ | - | - |
| Horário de Cobertura | _[Pendente — registros da FM-Rio]_ | - | - |
| Dias de Cobertura | _[Pendente — registros da FM-Rio]_ | - | - |
| Modalidade de Emprego | _[Pendente — registros da FM-Rio]_ | - | - |

## 4. Fatores de Incidência Criminal

Tabela com colunas **Fator identificado | Descrição | Responsável**, uma linha por item de `fatores` (use `tipo`, `contagem` e `orgao_responsavel`).

**Câmeras identificadas na área:** {total_cameras} câmeras.

## 5. Plano de Ação e Responsabilização

_Seção preenchida durante ou imediatamente após a reunião de CompStat, registrando os compromissos assumidos pelos gestores territoriais._

| Ação acordada | Responsável | Prazo | Status |
|---|---|---|---|
|  |  |  |  |
"""


async def stream_relatorio(slug: str):
    dimensoes = get_dimensoes(slug)
    if not dimensoes:
        yield f"data: {json.dumps({'error': 'Área não encontrada'})}\n\n"
        return

    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system = _build_system_prompt(dimensoes)

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": RELATORIO_PROMPT}],
    ) as stream:
        async for text in stream.text_stream:
            yield f"data: {json.dumps({'text': text})}\n\n"
    yield "data: [DONE]\n\n"


async def stream_chat(slug: str, relatorio_id: str, user_message: str):
    db = get_db()
    dimensoes = get_dimensoes(slug)

    msgs = db.execute(
        "SELECT role, conteudo FROM mensagens_relatorio WHERE relatorio_id = ? ORDER BY criado_em",
        (relatorio_id,),
    ).fetchall()
    history = [{"role": m["role"], "content": m["conteudo"]} for m in msgs]
    history.append({"role": "user", "content": user_message})

    # Persist user message BEFORE streaming starts
    db.execute(
        "INSERT INTO mensagens_relatorio (id, relatorio_id, role, conteudo) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), relatorio_id, "user", user_message),
    )
    db.commit()

    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system = _build_system_prompt(dimensoes) if dimensoes else "Analista CompStat Rio."

    full_response = ""
    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=history,
    ) as stream:
        async for text in stream.text_stream:
            full_response += text
            yield f"data: {json.dumps({'text': text})}\n\n"

    db.execute(
        "INSERT INTO mensagens_relatorio (id, relatorio_id, role, conteudo) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), relatorio_id, "assistant", full_response),
    )
    db.commit()
    yield "data: [DONE]\n\n"
