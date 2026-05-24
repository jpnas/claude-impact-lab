# Design: Arquitetura do Pipeline e Sistema CompStat Rio

**Data:** 2026-05-24
**Status:** Aprovado

---

## Contexto

O CompStat Municipal do Rio realiza reuniões semanais às terças-feiras presididas pelo Prefeito. O produto final é um sistema com dois modos de uso: (1) geração do Relatório Analítico de Área antes da reunião, e (2) um dashboard interativo usado durante a reunião para sanar dúvidas com dados visuais.

O pipeline de pré-processamento normaliza fontes heterogêneas (CSVs, shapefiles, DOCXs) em 6 **dimensões de análise** por área da Força Municipal (FM), persistidas no Supabase. O dashboard consome exclusivamente essas dimensões — sem processamento pesado em tempo real.

Hoje o sistema cobre 9 das 22 áreas FM. O pipeline é data-driven: descobre as áreas disponíveis via shapefile e processa todas sem necessidade de alteração de código quando novas áreas forem adicionadas.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js + TypeScript + TailwindCSS |
| Backend | FastAPI (Python) |
| Banco de dados | Supabase (PostgreSQL + Storage) |
| Pipeline | Script Python standalone |
| IA | Claude API (Anthropic) |

---

## Fluxo de Uso

### Modo 1 — Geração de Relatório (pré-reunião)

1. Analista acessa `/areas/{area}/relatorio`
2. Sistema chama `POST /areas/{area}/relatorio/gerar` → FastAPI lê as 6 dimensões do Supabase → monta prompt com contexto completo → chama Claude API em streaming (SSE)
3. Relatório é renderizado como artefato em tempo real
4. Analista refina via chat (`POST /areas/{area}/relatorio/chat`) — conversa multi-turn com relatório como contexto
5. Analista salva (`PUT /areas/{area}/relatorio`) → conteúdo persiste no Supabase
6. Relatório impresso é distribuído na reunião

### Modo 2 — Dashboard da Reunião

1. Usuário acessa `/areas/{area}/dashboard`
2. Frontend carrega `GET /areas/{area}/dimensoes` → renderiza heatmap, gráficos, mapas, tabelas
3. Relatório salvo exibido em painel lateral (`GET /areas/{area}/relatorio`)
4. Sem chamadas LLM — resposta instantânea a partir do cache

---

## Dimensões de Análise (6 por área)

### 1. Ocorrências (`ocorrencias`)
**Fase:** 1 (base determinística) + 2 (enriquecimento LLM via Disque Denúncia)

**Fontes:**
- `df_ocorrencias_tratado.csv` — 115k registros, spatial join com polígono FM
- `disk_denuncia.csv` — LLM extrai sinais criminais dos relatos filtrados

**Decisões de dados:**
- Janela temporal: **últimos 12 meses móveis** a partir da data de execução do pipeline
- Inclui variação percentual vs. os 12 meses anteriores (meses 13–24) para indicar tendência
- Pegadinha: `hora` e `dia_semana` têm 22 nulos — ignorar sem imputação
- Pegadinha: `locf` é o campo de logradouro (nome abreviado)

**Schema JSON:**
```json
{
  "total_periodo": 208,
  "variacao_yoy": "+12%",
  "periodo_referencia": "2024-05 a 2025-04",
  "por_tipo": { "Roubo a transeunte": 142, "Roubo de aparelho celular": 51 },
  "por_hora": { "00": 3, "21": 18 },
  "por_dia_semana": { "Segunda": 28, "Sexta": 38 },
  "periodo_predominante": "18h às 22h",
  "dia_critico": "Sexta",
  "hora_critica": "21h",
  "top_logradouros": [{ "nome": "Av. Presidente Vargas", "contagem": 47 }],
  "heatmap_points": [[-22.909, -43.180, 3.2]]
}
```

---

### 2. Dinâmica Criminal (`dinamica_criminal`)
**Fase:** 2 (LLM)

**Fontes:**
- RELINTs (`relints/*.docx`) — lidos via `zipfile` + `xml.etree` (sem python-docx)
- `disk_denuncia.csv` — top 40 relatos mais recentes de classes relevantes por área

**Decisão de dados Disque Denúncia:**
1. Deduplicar por `id_denuncia` (83k linhas → 18k denúncias reais)
2. Filtrar por `assuntos.classe` ∈ {CRIMES CONTRA O PATRIMÔNIO, SUBSTÂNCIAS ENTORPECENTES, ARMAS DE FOGO E ARTEFATOS EXPLOSIVOS}
3. Ordenar por `data_denuncia` DESC → top 40 por área
4. Pegadinha: `latitude`/`longitude` são strings com vírgula decimal (`-22,899555`) → `replace(',', '.')` antes de converter para float

**Contexto LLM:** recebe ORCRIM dominante de Contexto Territorial como background antes de sintetizar

**Schema JSON:**
```json
{
  "modalidade_predominante": "roubo oportunista a transeunte",
  "modus_operandi": "Indivíduos atuando a pé e em motocicletas...",
  "rotas_de_fuga": ["Av. Marechal Floriano sentido Rodoviária"],
  "pontos_de_receptacao": ["Camelódromo da Uruguaiana"],
  "perfil_suspeitos": "Jovens em duplas, a pé e em motocicletas",
  "orcrim_influencia": "TCP",
  "narrativa_completa": "A área analisada apresenta..."
}
```

---

### 3. Fatores Urbanos (`fatores_urbanos`)
**Fase:** 1 (base determinística) + 2 (enriquecimento LLM via RELINT)

**Fontes:**
- `fatores_urbanos.csv` — 2.085 pontos, filtro por `subarea_nome`
- RELINTs — LLM extrai fatores adicionais não cobertos pelo levantamento de campo

**Pegadinhas:**
- `coordenada_x` = latitude, `coordenada_y` = longitude (nomenclatura invertida na fonte)
- `subarea_nome` contém 23 áreas distintas + NaN; apenas 9 coincidem com áreas FM — os demais ~1.100 fatores são descartados por design

**Schema JSON:**
```json
{
  "fatores": [
    {
      "tipo": "Área mal iluminada com circulação de pedestres",
      "orgao_responsavel": "RioLuz",
      "contagem": 7,
      "pontos": [[-22.909, -43.180]]
    }
  ],
  "por_orgao": { "RioLuz": 7, "Comlurb": 6 },
  "fatores_adicionais_relint": ["Feiras livres sem licença concentradas no acesso ao metrô"]
}
```

---

### 4. Cobertura Operacional (`cobertura_operacional`)
**Fase:** 1 (determinística)

**Fontes:**
- `cameras_areas_fm.csv` — filtro por `nome_area_fm`
- `sh_area_forca/` — shapefile com polígonos FM

**Pegadinhas:**
- `geometry` das câmeras está em WKT string `POINT(lon lat)` → parsear com `shapely.wkt.loads()`
- Shapefile: encoding UTF-8 (não latin1); campo `nome_subar`

**Algoritmo de pontos cegos:**
1. A partir dos dados brutos de ocorrências (não do JSON de Ocorrências), agrupar por `locf` dentro do polígono FM e filtrar logradouros acima do percentil 80 de contagem
2. Para cada logradouro, verificar se há câmera em raio ≤ 100m (distância geodésica)
3. Logradouros sem câmera nesse raio = pontos cegos

*Nota: usa dados brutos para evitar dependência de ordenação com Ocorrências dentro da Fase 1.*

**Schema JSON:**
```json
{
  "poligono": { "type": "Polygon", "coordinates": [] },
  "cameras": [{ "id": "8f30106e-...", "lat": -22.909, "lon": -43.180 }],
  "total_cameras": 47,
  "pontos_cegos": [
    { "logradouro": "Rua Senador Pompeu", "contagem_crimes": 18, "cameras_proximas": 0 }
  ]
}
```

---

### 5. Contexto Territorial (`contexto_territorial`)
**Fase:** 1 (determinística)

**Fontes:**
- `dominio_territorial.csv` — 1.628 polígonos WKT de controle por ORCRIM
- `CPSR_2020_2022_2024.xlsx` — 23.332 registros PSR (censos 2020, 2022, 2024); ler com openpyxl

**Processamento:**
- Parsear polígonos WKT com shapely → spatial join com polígono FM → calcular proporção de área por ORCRIM
- Spatial join PSR com polígono FM → agregar por ano de censo

**Schema JSON:**
```json
{
  "orcrim_dominante": "TCP",
  "orcrim_por_tipo": { "TCP": 0.62, "CV": 0.21, "Milícia": 0.17 },
  "comunidades_proximas": ["Mangueira", "Providência"],
  "psr": {
    "total_2024": 47, "total_2022": 38, "total_2020": 29,
    "tendencia": "crescente",
    "pontos": [[-22.909, -43.180]]
  }
}
```

---

### 6. Coincidências (`coincidencias`)
**Fase:** 3 (LLM síntese — roda após todas as outras dimensões)

**Fontes:** as 5 dimensões anteriores da mesma área

**Algoritmo em duas etapas:**

**Etapa 1 — Cruzamento espacial (determinístico):**
1. Para cada logradouro em `top_logradouros` de Ocorrências:
   - Verificar fatores urbanos em raio ≤ 100m (de Fatores Urbanos)
   - Verificar se é ponto cego (de Cobertura Operacional)
2. Resultado: lista de trechos com `{crimes, fatores_proximos, ponto_cego}`

**Etapa 2 — Avaliação de relevância causal (LLM):**
- Contexto enviado: perfil criminal (tipo, horário, modus operandi), lista de trechos com fatores, ORCRIM dominante
- LLM avalia: quais fatores são causalmente relevantes para aquele padrão específico de crime (ex: iluminação só é relevante se o pico for noturno)
- LLM gera: justificativa operacional por trecho + recomendações para as 4 perguntas norteadoras

**Fórmula do `score_prioridade`:**
`score = (crimes / max_crimes_area) * 0.5 + (n_fatores_relevantes / max_fatores_area) * 0.3 + (ponto_cego ? 0.2 : 0)`

Normalizado entre 0 e 1. Pesos: volume criminal (50%), fatores relevantes (30%), ausência de câmera (20%).

**Princípio:** o LLM não descobre trechos críticos — ele avalia e explica. A descoberta é determinística na Etapa 1, garantindo auditabilidade.

**Schema JSON:**
```json
{
  "trechos_criticos": [
    {
      "logradouro": "Rua Senador Pompeu",
      "score_prioridade": 0.92,
      "crimes_no_periodo": 18,
      "ponto_cego": true,
      "fatores_relevantes": [
        {
          "tipo": "Área mal iluminada",
          "orgao": "RioLuz",
          "relevancia": "Alta incidência noturna — 78% dos crimes entre 19h e 23h"
        }
      ],
      "justificativa": "Trecho concentra 18 roubos a transeunte, opera sem cobertura de câmera, e possui 2 pontos de iluminação inativa — condição diretamente favorável ao modus operandi identificado."
    }
  ],
  "recomendacoes": {
    "rota_fm": "Concentrar patrulha no eixo Rua Senador Pompeu – Av. Presidente Vargas das 19h às 23h",
    "horario_patrulhamento": "19h–23h",
    "modelo_emprego": "Dupla a pé + viatura de apoio",
    "acoes_municipais": [
      { "orgao": "RioLuz", "acao": "Reativar 2 pontos de iluminação na Rua Senador Pompeu" }
    ]
  }
}
```

---

## Pipeline — Estrutura de Fases

```
Fase 1 — Determinística (segundos)
  Para cada área descoberta via shapefile:
    → Ocorrências base: spatial join + agregações (12 meses móveis + YoY)
    → Fatores Urbanos base: filtro subarea_nome + agrupamento
    → Cobertura Operacional: câmeras + polígono + pontos cegos (raio 100m)
    → Contexto Territorial: ORCRIM proporcional + PSR por censo

Fase 2 — LLM paralelo (minutos)
  Para cada área (pode rodar em paralelo entre áreas):
    → Ocorrências enrich: LLM extrai sinais do Disque Denúncia filtrado
    → Dinâmica Criminal: LLM sintetiza RELINT + top 40 relatos DD
    → Fatores Urbanos enrich: LLM extrai fatores adicionais do RELINT

Fase 3 — LLM síntese (após Fase 2)
  Para cada área:
    → Coincidências: cruzamento espacial + LLM avalia relevância causal
```

---

## Schema Supabase

```sql
areas
  id uuid PK
  nome text          -- nome completo da área FM
  slug text          -- url-friendly (ex: presidente-vargas)

reunioes
  id uuid PK
  data_reuniao date  -- terça-feira do ciclo
  criado_em timestamp

dimensoes_analise
  id uuid PK
  area_id uuid FK → areas
  tipo text          -- enum: ocorrencias | dinamica_criminal | fatores_urbanos
                     --       cobertura_operacional | contexto_territorial | coincidencias
  dados jsonb
  referencia_pipeline timestamp  -- quando o pipeline que gerou esses dados rodou

relatorios
  id uuid PK
  area_id uuid FK → areas
  reuniao_id uuid FK → reunioes
  conteudo text      -- markdown do relatório finalizado
  status text        -- enum: rascunho | finalizado
  criado_em timestamp
  atualizado_em timestamp

mensagens_relatorio
  id uuid PK
  relatorio_id uuid FK → relatorios
  role text          -- enum: user | assistant
  conteudo text
  criado_em timestamp
```

---

## API FastAPI — Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/areas` | Lista áreas com cache disponível |
| GET | `/areas/{slug}/dimensoes` | Retorna as 6 dimensões do cache |
| POST | `/areas/{slug}/relatorio/gerar` | Inicia geração do relatório (streaming SSE) |
| POST | `/areas/{slug}/relatorio/chat` | Envia prompt de ajuste (streaming SSE) |
| GET | `/areas/{slug}/relatorio` | Recupera relatório salvo (por reunião) |
| PUT | `/areas/{slug}/relatorio` | Salva relatório finalizado |

---

## Rotas Frontend

| Rota | Modo | Descrição |
|---|---|---|
| `/` | — | Seleção de área e reunião |
| `/areas/{slug}/relatorio` | Modo 1 | Chat + artifact para gerar e ajustar relatório |
| `/areas/{slug}/dashboard` | Modo 2 | Dashboard da reunião com visualizações e relatório salvo |

---

## Decisões Fixadas

| Decisão | Valor |
|---|---|
| Janela temporal ocorrências | Últimos 12 meses móveis |
| Comparativo temporal | Variação % vs. 12 meses anteriores |
| Raio pontos cegos / fatores | 100 metros |
| Filtro Disque Denúncia | Deduplicar → 3 classes criminais → top 40 recentes |
| Lat/lon DD | `replace(',', '.')` antes de `float()` |
| Geometria câmeras | `shapely.wkt.loads()` no campo `geometry` |
| Shapefile encoding | UTF-8; campo `nome_subar` |
| Leitura RELINT | `zipfile` + `xml.etree` (sem python-docx) |
| PSR Excel | `openpyxl` |
| Autenticação MVP | Nenhuma — acesso único |
| Áreas no pipeline | Data-driven via shapefile (não hardcoded) |
