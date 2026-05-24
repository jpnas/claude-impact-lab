# CompStat Rio — Plataforma de Inteligência Criminal

Plataforma de inteligência territorial desenvolvida para o **Hackathon Anthropic 2026**, em parceria com a **Secretaria-Geral do CompStat Municipal da Prefeitura do Rio de Janeiro**.

🎬 **[Assista à demo (vídeo)](https://youtu.be/Vvt6m8fRjAg)**

O CompStat Municipal realiza reuniões semanais (terças-feiras) presididas pelo Prefeito. O analista usa esta plataforma para preparar a reunião e gerar automaticamente o **Relatório Analítico de Área** distribuído no encontro.

## O Problema

A cada ciclo semanal, a equipe precisa produzir um Relatório Analítico por polígono de segurança. O gargalo é a síntese: ocorrências georreferenciadas, denúncias (Disque Denúncia), relatórios de inteligência de campo (RELINTs) e fatores urbanos (iluminação, vegetação, desordem) vivem em silos. Cruzar essas camadas manualmente consome horas.

## A Solução

Um **pipeline** normaliza as 5 fontes em 6 dimensões de análise por área e persiste em SQLite. Um **dashboard web** lê essas dimensões e, sob demanda, usa o Claude para gerar o relatório e responder perguntas em chat multi-turno.

---

## Arquitetura

São **3 componentes**. Em runtime, a fonte de dados é o SQLite **`compstat.db`** (já versionado no repo, populado) — Supabase **não** é necessário para rodar.

```
pipeline/  →  compstat.db (SQLite)  ←  backend/ (FastAPI)  ←  frontend/ (Next.js)
 (offline)        (versionado)            uvicorn :8000          npm dev :3000
```

| Componente | Stack | Papel |
|---|---|---|
| `pipeline/` | Python (shapely, pyshp, pandas, anthropic) | Processa as fontes e popula `compstat.db`. Roda offline, antes da reunião. **Opcional** para só rodar a app. |
| `backend/` | FastAPI + SQLite + Claude API | Serve as dimensões e faz streaming (SSE) da geração de relatório e do chat. |
| `frontend/` | Next.js 16 + React 19 + Tailwind 4 | Dashboard: seleção de área → 6 dimensões → geração de relatório + chat. |

> O `compstat.db` já vem pronto no repositório (8 áreas, 6 dimensões cada). **Não é preciso clonar o repo de dados nem rodar o pipeline** para subir a aplicação — só para regenerar os dados (ver final).

A ideia central é separar o **trabalho pesado e caro** (cruzar fontes heterogêneas, chamar o Claude para sintetizar inteligência) do **uso em tempo real** na reunião. O pipeline faz esse trabalho uma vez por ciclo e materializa o resultado em 6 dimensões por área no SQLite. Em runtime, o backend só lê dimensões já prontas — o Claude só volta a ser acionado quando o analista pede o relatório ou conversa com ele.

### Fluxo ponta a ponta

```
 FONTES                       PIPELINE (offline)                 BANCO              RUNTIME
 ──────                       ──────────────────                 ─────              ───────
 ocorrências CSV   ─┐   Fase 1: determinística                                ┌─ dashboard
 fatores CSV        │     ocorrencias / fatores                                │   (6 dimensões
 câmeras CSV        ├──▶   cobertura / contexto    ──▶ dimensoes_  ──▶ FastAPI ─┤    + heatmap)
 shapefile (8 pol.) │   Fase 2: enriquecimento LLM      analise            │   │
 Disque Denúncia    │     ocorrências+DD, fatores+      (6 por área)       │   └─ relatório
 RELINTs (DOCX)    ─┘     RELINT, dinâmica criminal   compstat.db          │      (stream SSE
                       Fase 3: síntese LLM                                 │       + chat Claude)
                         coincidências + recomendações ──────────────▶ Claude API ◀┘
```

#### 1. Ingestão e processamento (`pipeline/run_pipeline.py`)

`load_areas()` lê os **8 polígonos** da Força Municipal do shapefile. Para cada área, os *processadores* (`pipeline/processadores/`) rodam em **3 fases** e o resultado de cada um é gravado como uma linha em `dimensoes_analise` (`upsert_dimensao`, com `ON CONFLICT(area_id, tipo)` — reprocessar sobrescreve):

- **Fase 1 — determinística (sem LLM):** filtra cada fonte pelo polígono da área e agrega.
  - `ocorrencias` — contagens por tipo, distribuição por hora/dia, hora e dia críticos, top logradouros e pontos do heatmap (das 115k ocorrências georreferenciadas).
  - `fatores_urbanos` — fatores por tipo e órgão responsável.
  - `cobertura_operacional` — câmeras, polígono da FM e pontos cegos.
  - `contexto_territorial` — domínio de ORCRIM (CV/TCP/Milícia/ADA) e PSR.
- **Fase 2 — enriquecimento via Claude:** cruza as bases da Fase 1 com fontes textuais/qualitativas.
  - `enrich_ocorrencias_dd` agrega o **Disque Denúncia** (deduplicado por `id_denuncia`, filtrado por classe criminal e por polígono).
  - `enrich_fatores_relint` extrai fatores adicionais dos **RELINTs** (DOCX lido via `zipfile`).
  - `build_dinamica_criminal` sintetiza RELINTs + Disque Denúncia em uma narrativa de *modus operandi*, modalidade, rotas de fuga e pontos de receptação.
- **Fase 3 — síntese final via Claude (`coincidencias`):** cruzamento espacial **determinístico** (proximidade entre top logradouros, fatores urbanos e pontos cegos → `score_prioridade`) seguido de uma **avaliação causal pelo Claude** (qual fator é realmente relevante para o padrão de crime), produzindo os trechos críticos priorizados e as recomendações operacionais (rota, horário, modelo de emprego, ações municipais).

Saída: **`compstat.db`** com 8 áreas × 6 dimensões. O pipeline não derruba a aplicação — só atualiza as linhas das dimensões.

#### 2. Persistência (`compstat.db`, schema em `backend/db.py`)

SQLite versionado no repo. Tabelas principais: `areas` (as 8 áreas, com `slug`), `dimensoes_analise` (o cache do pipeline — `tipo` ∈ as 6 dimensões, `dados` em JSON), `relatorios` (rascunho/finalizado por área) e `mensagens_relatorio` (histórico do chat multi-turno). O schema é criado e as áreas são semeadas no primeiro acesso (`get_db`).

#### 3. Backend (`backend/`, FastAPI)

Leitura barata, escrita cara só sob demanda:

- `GET /areas/{slug}/dimensoes` (`services/dimensoes.py`) apenas desserializa o JSON das 6 dimensões do banco — **zero processamento pesado, zero Claude**.
- `POST .../relatorio/gerar` (`services/relatorio.py`) monta um *system prompt* com as 6 dimensões da área — **compactando arrays de coordenadas para contagens** (`_compactar`, evita estourar o contexto) — e envia o **template oficial** do Relatório Analítico de Área ao Claude. Regras de integridade no prompt **proíbem inventar dados**: campos sem fonte recebem o marcador `_[Pendente — registros da FM-Rio]_`. A resposta é transmitida **token a token via SSE** (`AsyncAnthropic.messages.stream`).
- `POST .../relatorio/chat` mantém conversa multi-turno sobre o relatório, com o mesmo contexto das dimensões; cada mensagem (usuário e assistente) é persistida em `mensagens_relatorio`.

#### 4. Frontend (`frontend/`, Next.js + React)

O analista navega: **homepage** (seletor das 8 áreas, `cache_disponivel` indica quais já têm dimensões) → **dashboard** da área (`/areas/[slug]/dashboard` — as 6 dimensões em cards + mapa de calor das ocorrências) → **relatório** (`/areas/[slug]/relatorio`). Na página de relatório, o botão "Gerar" abre o stream SSE e o texto do Claude aparece em tempo real no artifact; ao lado, o painel de chat permite refinar e questionar o relatório. O cliente (`lib/api.ts`) consome o SSE lendo o `ReadableStream` e parseando as linhas `data:`.

---

## Pré-requisitos

- **Python 3.11+**
- **Node.js 20+**
- Uma **API key da Anthropic** (`ANTHROPIC_API_KEY`) — necessária para gerar relatórios e usar o chat. O dashboard e as 6 dimensões funcionam sem a key; só a geração via Claude exige.

---

## Rodando a aplicação

### 1. Clonar

```bash
git clone <url-do-repo> claude-impact-lab
cd claude-impact-lab
```

### 2. Backend (FastAPI)

A partir da **raiz do repositório**:

```bash
python -m venv .venv
source .venv/bin/activate          # fish: source .venv/bin/activate.fish

pip install -r backend/requirements.txt

cp .env.example .env               # edite e coloque sua ANTHROPIC_API_KEY
uvicorn backend.main:app --reload --port 8000
```

> O backend precisa ser iniciado da raiz (módulo `backend.main:app`) por causa dos imports `from backend...`. Health check: http://localhost:8000/health

`.env` (a partir de `.env.example`):

```
ANTHROPIC_API_KEY=sk-ant-...        # obrigatória para gerar relatório / chat
DB_PATH=./compstat.db               # default; já aponta para o banco versionado
DATA_ROOT=../claude_impact_lab_compstat_rio   # só usado pelo pipeline
```

### 3. Frontend (Next.js)

Em outro terminal:

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Abra **http://localhost:3000**.

---

## API (backend)

| Método | Rota | Descrição |
|---|---|---|
| `GET`  | `/health` | Health check |
| `GET`  | `/areas` | Lista as 8 áreas (com `cache_disponivel`) |
| `GET`  | `/areas/{slug}/dimensoes` | As 6 dimensões da área |
| `POST` | `/areas/{slug}/relatorio/gerar` | Gera o relatório (stream SSE) |
| `POST` | `/areas/{slug}/relatorio/chat` | Chat multi-turno sobre o relatório (stream SSE) |
| `GET`  | `/areas/{slug}/relatorio` | Recupera relatório salvo |
| `PUT`  | `/areas/{slug}/relatorio` | Salva/finaliza o relatório |

As 6 dimensões por área: `ocorrencias`, `dinamica_criminal`, `fatores_urbanos`, `cobertura_operacional`, `contexto_territorial`, `coincidencias`.

---

## Regenerar os dados (pipeline — opcional)

Só é necessário se quiser reprocessar as fontes do zero. Requer o **repositório de dados** clonado ao lado deste:

```bash
# ao lado de claude-impact-lab/
git clone https://github.com/jpnas/claude_impact_lab_compstat_rio
```

Depois, da raiz deste repo (com a venv ativa e `ANTHROPIC_API_KEY` no `.env`):

```bash
pip install -r pipeline/requirements.txt
python -m pipeline.run_pipeline
```

Isso reconstrói o `compstat.db`. O caminho do repo de dados é configurável via `DATA_ROOT` no `.env`.

Fontes processadas: ocorrências criminais (CSV), polígonos da Força Municipal (Shapefile), fatores urbanos (CSV), Disque Denúncia (CSV) e RELINTs (DOCX). Detalhes em `CLAUDE.md` e `brainstorming/`.

---

Hackathon Anthropic 2026 | Prefeitura do Rio de Janeiro
