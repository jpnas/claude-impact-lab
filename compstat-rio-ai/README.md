# CompStat Rio AI

PWA/dashboard de inteligência criminal para o CompStat Municipal do Rio. O MVP cruza ocorrências criminais, fatores urbanos, inteligência territorial, polígonos operacionais simulados e relatórios qualitativos mockados para apoiar decisões de patrulhamento e zeladoria urbana.

Subtítulo do produto: **Sala de Situação Conversacional para Inteligência Territorial**.

## Problema

Gestores municipais precisam decidir rapidamente onde atuar, em qual horário e com quais órgãos. Hoje, a leitura de ocorrências, fatores urbanos e inteligência territorial costuma ficar fragmentada, atrasando a reunião CompStat e a resposta operacional.

## Solução

O CompStat Rio AI entrega uma sala de situação conversacional com:

- Dashboard de indicadores críticos.
- Visualização territorial dos trechos de risco.
- Motor de "Bingo" para detectar convergência entre camadas.
- Chat operacional com Claude API ou resposta mockada inteligente.
- Plano de ação intersetorial com responsável, prioridade, justificativa e prazo.
- Endpoint de relatório executivo para integração com outros sistemas.

## Stack

- Next.js App Router
- TypeScript sem `any`
- TailwindCSS
- FastAPI como backend principal
- API routes do Next.js como proxy/fallback local
- PWA com `manifest.json`
- Vitest + Testing Library
- Dados mockados em JSON local
- Claude API opcional via `ANTHROPIC_API_KEY`

## Como Rodar Com FastAPI

```bash
cd ../compstat-rio-ai-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Em outro terminal:

```bash
cd compstat-rio-ai
pnpm install
pnpm dev
```

Acesse `http://localhost:3000` ou a porta indicada pelo Next. Se a porta 3000 estiver ocupada, use `http://localhost:3001`.

Para testar em outro dispositivo da rede, use o IP mostrado pelo Next e mantenha o FastAPI rodando na porta `8000`.

Também existem comandos equivalentes:

```bash
pnpm test
pnpm build
```

Backend:

```bash
cd ../compstat-rio-ai-api
.venv/bin/pytest
```

## Variáveis de Ambiente

Crie `.env.local` somente se quiser usar Claude real:

```bash
ANTHROPIC_API_KEY=sua_chave_aqui
FASTAPI_URL=http://localhost:8000
```

Sem essa variável, o chat responde com mock inteligente seguindo sempre:

- Diagnóstico
- Evidências
- Recomendação operacional
- Órgãos responsáveis

## Testes Para a Banca

Rodar suíte completa:

```bash
pnpm test
```

O que está coberto:

- Cálculo do score total.
- Classificação de risco: baixo, médio, alto e crítico.
- Regra de "BINGO" com pelo menos 3 camadas acima de 20 pontos.
- Geração de resumo executivo.
- Plano de ação operacional.
- Resposta mockada do chat no formato obrigatório.
- Renderização dos cards, mapa fake e tabela de ações.

## Endpoints

Backend FastAPI:

```bash
GET http://localhost:8000/health
GET http://localhost:8000/area
GET http://localhost:8000/summary
GET http://localhost:8000/action-plan
POST http://localhost:8000/chat
```

Resumo executivo:

```bash
GET /api/summary
```

Retorna:

- resumo executivo
- área prioritária
- horário crítico
- bingo identificado
- recomendações principais

Plano de ação:

```bash
GET /api/action-plan
```

Chat:

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Onde a FM deve atuar hoje à noite?"
}
```

As rotas `/api/*` do Next chamam o FastAPI quando ele está disponível. Se o backend estiver fora do ar, usam o fallback local para preservar a demo.

Perguntas demonstráveis:

- Onde a FM deve atuar hoje à noite?
- Qual o horário de maior risco?
- Quais órgãos precisam agir?
- Gere um resumo executivo.
- Qual o plano de ação?

## Motor de Bingo

Regra de score:

```text
score_total = crime_score + urban_factor_score + intelligence_score + temporal_score
```

Classificação:

- 0-39: baixo
- 40-69: médio
- 70-100: alto
- acima de 100: crítico

BINGO:

- quando pelo menos 3 camadas estão acima de 20 pontos.

## Dados Mockados

Arquivo principal:

```bash
data/mock-area.json
```

Área demonstrada:

```text
Rua Lauro Müller – Avenida General Severiano – Avenida Venceslau Brás
```

Trechos críticos:

- Rua Lauro Müller
- Avenida General Severiano
- Avenida Venceslau Brás

## Pitch

O CompStat Rio AI transforma a reunião operacional em uma experiência orientada por evidências. Em vez de abrir múltiplas planilhas e relatórios, o gestor vê onde está o risco, entende por que ele ocorre, conversa com uma IA e recebe um plano acionável por órgão municipal. O resultado é menos tempo de consolidação manual e mais foco em decisão, coordenação e execução territorial.
