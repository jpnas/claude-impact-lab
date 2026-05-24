# CompStat Rio — Plataforma de Inteligência Criminal

Plataforma de inteligência territorial desenvolvida para o **Hackathon Anthropic 2026**, em parceria com a **Secretaria-Geral do CompStat Municipal da Prefeitura do Rio de Janeiro**.

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
