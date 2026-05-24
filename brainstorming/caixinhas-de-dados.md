# Arquitetura de Dados: as "Caixinhas"

## Contexto

O problema central do CompStat é que os dados relevantes para a reunião semanal vivem em fontes heterogêneas e desconectadas — CSVs estruturados, shapefiles, documentos DOCX e texto livre. Para produzir o Relatório Analítico de Área, um analista hoje compila tudo isso manualmente, o que toma horas.

A solução passa por um pipeline de pré-processamento que lê todas essas fontes e as normaliza em estruturas unificadas por área da FM. Chamamos essas estruturas de **caixinhas**.

Cada caixinha representa uma dimensão de análise que o relatório precisa. Ao final do processamento, cada uma das 8 áreas da FM tem 5 caixinhas populadas — e o dashboard lê dessas caixinhas para exibir os dados e gerar o relatório.

---

## As 5 Caixinhas

### 1. Ocorrências

**O que guarda:** volume de crimes, distribuição temporal, ranking por logradouro, tipos de delito.

**Para que serve no relatório:**
- Indicadores do Período (total de roubos/furtos, ranking entre áreas)
- Distribuição por Tipo de Ocorrência
- Análise Temporal (matriz hora × dia da semana, período predominante, dia/horário crítico)
- Mapa de calor (heatmap de densidade criminal)

**Natureza:** híbrida — quantitativa + qualitativa

**Fontes:**

| Fonte | Tipo | Como alimenta | Processamento |
|---|---|---|---|
| `df_ocorrencias_tratado.csv` | Estruturada | Principal — 115k registros com lat/long, hora, dia, tipo | Spatial join com polígono FM |
| `disk_denuncia.csv` | Não-estruturada | Complementar — relatos que descrevem crimes com local e horário | LLM extrai: local mencionado, horário, tipo de crime |

**Output esperado (JSON por área):**
```json
{
  "total_roubos": 208,
  "total_furtos": 0,
  "por_tipo": {
    "Roubo a transeunte": 142,
    "Roubo de aparelho celular": 51,
    "Roubo em coletivo": 15
  },
  "por_hora": { "00": 3, "01": 1, ..., "21": 18, "22": 14 },
  "por_dia_semana": { "Segunda": 28, "Terça": 31, ... },
  "periodo_predominante": "18h às 22h",
  "dia_critico": "Sexta",
  "hora_critica": "21h",
  "top_logradouros": [
    { "nome": "Av. Presidente Vargas", "contagem": 47 },
    { "nome": "Campo de Santana", "contagem": 31 }
  ],
  "heatmap_points": [[lat, lon, weight], ...]
}
```

---

### 2. Dinâmica Criminal

**O que guarda:** síntese qualitativa de como o crime acontece — modus operandi, rotas de fuga, pontos de receptação, perfil de suspeitos, influência de organizações criminosas (ORCRIM).

**Para que serve no relatório:**
- Seção "Dinâmica Criminal" (texto narrativo)
- Resposta à pergunta norteadora 3: modelo de emprego da FM (moto, viatura, a pé)
- Campo "Área sob influência de grupo criminoso" na identificação

**Natureza:** predominantemente qualitativa (LLM)

**Fontes:**

| Fonte | Tipo | Como alimenta | Processamento |
|---|---|---|---|
| `relints/*.docx` | Não-estruturada | Principal — texto rico com modus operandi, rotas, ORCRIM | LLM sintetiza em JSON estruturado |
| `disk_denuncia.csv` (relato_redacted) | Não-estruturada | Complementar — relatos de cidadãos confirmando padrões | LLM extrai padrões recorrentes por área |

**Nota sobre o Disque Denúncia:** o CSV tem 83.549 linhas mas apenas 18.003 denúncias reais — o arquivo veiu desnormalizado de um JSON, com linhas extras para órgãos, assuntos e envolvidos. O processamento deve deduplicar por `id_denuncia`.

**Output esperado (JSON por área):**
```json
{
  "modalidade_predominante": "furto oportunista a transeunte",
  "modus_operandi": "Indivíduos atuando a pé e em motocicletas aproveitam momentos de distração em acessos ao transporte público. Ações em grupo, com um abordando a vítima e outro aguardando na moto para fuga.",
  "rotas_de_fuga": ["Av. Marechal Floriano sentido Rodoviária", "Vias transversais da Av. Presidente Vargas"],
  "pontos_de_receptacao": ["Camelódromo da Uruguaiana"],
  "perfil_suspeitos": "Indivíduos jovens, atuando em duplas ou grupos, a pé e em motocicletas",
  "narrativa_completa": "A área analisada apresenta..."
}
```

---

### 3. Fatores Urbanos

**O que guarda:** lista de problemas urbanos identificados na área, com tipo, localização e órgão municipal responsável por resolver.

**Para que serve no relatório:**
- Seção "Fatores de Incidência Criminal"
- Resposta à pergunta norteadora 4: como os órgãos devem resolver os fatores urbanos
- Insumo para o Painel de Coincidências (cruzamento com mancha criminal)

**Natureza:** híbrida — estruturada + complemento qualitativo via LLM

**Fontes:**

| Fonte | Tipo | Como alimenta | Processamento |
|---|---|---|---|
| `fatores_urbanos.csv` | Estruturada | Principal — 2.085 pontos com tipo, coordenada e órgão responsável | Filtro por `subarea_nome` (já mapeado para área FM) |
| `relints/*.docx` | Não-estruturada | Complementar — menciona fatores não cobertos pelo levantamento de campo | LLM extrai fatores adicionais citados |

**Output esperado (JSON por área):**
```json
{
  "fatores": [
    {
      "tipo": "Área mal iluminada com circulação de pedestres",
      "orgao_responsavel": "RioLuz",
      "contagem": 7,
      "pontos": [[lat, lon], ...]
    },
    {
      "tipo": "Vegetação encobrindo iluminação pública",
      "orgao_responsavel": "Comlurb",
      "contagem": 4,
      "pontos": [[lat, lon], ...]
    }
  ],
  "por_orgao": {
    "RioLuz": 7,
    "Comlurb": 6,
    "SEOP": 3
  }
}
```

---

### 4. Cobertura Operacional

**O que guarda:** câmeras de vigilância na área, polígono de atuação da FM, e pontos cegos (trechos com alta incidência criminal sem cobertura de câmera).

**Para que serve no relatório:**
- Seção "Câmeras identificadas na área"
- Insumo para o mapa (sobreposição de câmeras com heatmap)
- Painel de Coincidências (trechos críticos sem câmera = prioridade de ação)
- Resposta à pergunta norteadora 1: rota da FM

**Natureza:** quantitativa — processamento puramente determinístico, sem LLM

**Fontes:**

| Fonte | Tipo | Como alimenta | Processamento |
|---|---|---|---|
| `cameras_areas_fm.csv` | Estruturada | 985 câmeras com coordenada e nome da área | Filtro por `nome_area_fm` |
| `sh_area_forca/` | Geoespacial | Polígonos das 8 áreas FM | Âncora geoespacial — todos os spatial joins partem daqui |

**Output esperado (JSON por área):**
```json
{
  "poligono": { "type": "Polygon", "coordinates": [...] },
  "cameras": [
    { "id": "8f30106e-...", "lat": -22.909, "lon": -43.180, "trecho": 203724 }
  ],
  "total_cameras": 47,
  "pontos_cegos": [
    { "logradouro": "Rua Senador Pompeu", "contagem_crimes": 18, "cameras_proximas": 0 }
  ]
}
```

---

### 5. Contexto Territorial

**O que guarda:** domínio territorial de organizações criminosas (ORCRIM) sobre a área e densidade de Pessoas em Situação de Rua (PSR).

**Para que serve no relatório:**
- Campo "Área sob influência de grupo criminoso" na identificação da área
- Seção "Contexto Territorial" — background estrutural que enquadra a dinâmica criminal
- Insumo para o LLM ao gerar a narrativa de Dinâmica Criminal (Caixinha 2): saber qual facção domina o território ajuda a contextualizar o modus operandi

**Natureza:** quantitativa — processamento puramente determinístico, sem LLM

**Fontes:**

| Fonte | Tipo | Como alimenta | Processamento |
|---|---|---|---|
| `dominio_territorial.csv` | Geoespacial | 1.628 polígonos de controle por facção (CV, TCP, Milícia, ADA) | Spatial join com polígono FM; identifica ORCRIM dominante |
| `CPSR_2020_2022_2024.xlsx` | Estruturada | 23.332 registros de PSR com lat/long (censos 2020, 2022, 2024) | Spatial join com polígono FM; agrega por densidade e evolução temporal |

**Output esperado (JSON por área):**
```json
{
  "orcrim_dominante": "TCP",
  "orcrim_por_tipo": {
    "TCP": 0.62,
    "CV": 0.21,
    "Milícia": 0.17
  },
  "comunidades_proximas": ["Mangueira", "Providência"],
  "psr": {
    "total_2024": 47,
    "total_2022": 38,
    "total_2020": 29,
    "tendencia": "crescente",
    "pontos": [[lat, lon], ...]
  }
}
```

---

## Fluxo do Pipeline

```
FONTES BRUTAS
    ↓
pipeline.py  (roda uma vez, antes da reunião de terça)
    ↓
Para cada uma das 8 áreas FM:
    ├── Spatial join → Caixinha 1 (Ocorrências) + Caixinha 4 (Cobertura Operacional)
    ├── LLM (Claude) → Caixinha 2 (Dinâmica Criminal)
    ├── Filtro + Spatial join → Caixinha 3 (Fatores Urbanos)
    └── Spatial join → Caixinha 5 (Contexto Territorial)
    ↓
cache/
    ├── presidente_vargas/
    │   ├── ocorrencias.json
    │   ├── dinamica_criminal.json
    │   ├── fatores_urbanos.json
    │   ├── cobertura_operacional.json
    │   └── contexto_territorial.json
    └── ... (8 pastas)
    ↓
DASHBOARD (Streamlit)
    ├── Lê os JSONs do cache
    ├── Exibe mapas, gráficos, tabelas e texto por área
    └── Botão "Gerar Relatório" → Claude preenche template → PDF/DOCX
```

---

## Decisões tomadas

**Por que pré-computar e não processar on-demand?**
Os dados mudam semanalmente. O pipeline roda na segunda-feira; na terça, o dashboard está pronto e rápido. Chamadas ao LLM ficam fora do caminho crítico da reunião.

**Por que Contexto Territorial é uma caixinha separada e não parte da Caixinha 2 (Dinâmica Criminal)?**
São dimensões com naturezas e ritmos diferentes. ORCRIM e PSR são dados estruturais — mudam lentamente e vêm de fontes determinísticas (polígonos de domínio territorial, censo PSR). Dinâmica Criminal é uma síntese qualitativa que requer LLM. Misturá-los forçaria processamento LLM em dados que não precisam dele, e dificultaria reusar o contexto territorial em outras partes do dashboard (como o cabeçalho do relatório e o painel de coincidências). A Caixinha 5 alimenta a Caixinha 2 como input: o LLM recebe o ORCRIM dominante como contexto antes de sintetizar a narrativa de dinâmica criminal.

**Por que PSR está na Caixinha 5 (Contexto Territorial) e não na Caixinha 3 (Fatores Urbanos)?**
PSR é um dado demográfico-territorial com série histórica (2020, 2022, 2024) — informa o contexto estrutural da área, não um fator pontual a ser resolvido por um órgão municipal. Tratar PSR como fator urbano ao lado de "poste quebrado" distorce o peso analítico e complica a responsabilização operacional.

**Por que o Disque Denúncia aparece em duas caixinhas?**
Porque o mesmo relato pode descrever um crime ocorrido (Caixinha 1) e o padrão de como ele ocorre (Caixinha 2). O LLM processa o texto uma vez e extrai as duas dimensões simultaneamente.
