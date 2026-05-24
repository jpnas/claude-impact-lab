# Arquitetura de Dados: as "Caixinhas"

## Contexto

O problema central do CompStat é que os dados relevantes para a reunião semanal vivem em fontes heterogêneas e desconectadas — CSVs estruturados, shapefiles, documentos DOCX e texto livre. Para produzir o Relatório Analítico de Área, um analista hoje compila tudo isso manualmente, o que toma horas.

A solução passa por um pipeline de pré-processamento que lê todas essas fontes e as normaliza em estruturas unificadas por área da FM. Chamamos essas estruturas de **caixinhas**.

Cada caixinha representa uma dimensão de análise que o relatório precisa. Ao final do processamento, cada uma das 8 áreas da FM tem 4 caixinhas populadas — e o dashboard lê dessas caixinhas para exibir os dados e gerar o relatório.

---

## As 4 Caixinhas

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

**Natureza:** híbrida — predominantemente qualitativa (LLM) com um campo estruturado (ORCRIM via spatial join)

**Fontes:**

| Fonte | Tipo | Como alimenta | Processamento |
|---|---|---|---|
| `relints/*.docx` | Não-estruturada | Principal — texto rico com modus operandi, rotas, ORCRIM, PSR | LLM sintetiza em JSON estruturado |
| `disk_denuncia.csv` (relato_redacted) | Não-estruturada | Complementar — relatos de cidadãos confirmando padrões | LLM extrai padrões recorrentes por área |
| `dominio_territorial.csv` | Estruturada | ORCRIM — polígonos de controle por facção (CV, TCP, Milícia, ADA) | Spatial join com polígono FM |

**Nota sobre o Disque Denúncia:** o CSV tem 83.549 linhas mas apenas 18.003 denúncias reais — o arquivo veio desnormalizado de um JSON, com linhas extras para órgãos, assuntos e envolvidos. O processamento deve deduplicar por `id_denuncia`.

**Output esperado (JSON por área):**
```json
{
  "modalidade_predominante": "furto oportunista a transeunte",
  "modus_operandi": "Indivíduos atuando a pé e em motocicletas aproveitam momentos de distração em acessos ao transporte público. Ações em grupo, com um abordando a vítima e outro aguardando na moto para fuga.",
  "rotas_de_fuga": ["Av. Marechal Floriano sentido Rodoviária", "Vias transversais da Av. Presidente Vargas"],
  "pontos_de_receptacao": ["Camelódromo da Uruguaiana"],
  "perfil_suspeitos": "Indivíduos jovens, atuando em duplas ou grupos, a pé e em motocicletas",
  "orcrim": "TCP",
  "comunidades_proximas": ["Mangueira", "Providência"],
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
| `CPSR_2020_2022_2024.xlsx` | Estruturada | PSR — 23.332 registros todos com lat/long (2020, 2022, 2024) | Spatial join com polígono FM; agrega por densidade |
| `relints/*.docx` | Não-estruturada | Complementar — menciona fatores não cobertos pelo levantamento de campo | LLM extrai fatores adicionais citados |

**Nota sobre PSR:** apesar de ser um dado demográfico, o PSR entra nesta caixinha porque aparece como **fator de incidência criminal** no relatório — com responsável definido (SMAS) e na mesma seção que iluminação e vegetação.

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
    },
    {
      "tipo": "Pessoas em situação de rua",
      "orgao_responsavel": "SMAS",
      "contagem": 12,
      "pontos": [[lat, lon], ...]
    }
  ],
  "por_orgao": {
    "RioLuz": 7,
    "Comlurb": 6,
    "SMAS": 12,
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

## Fluxo do Pipeline

```
FONTES BRUTAS
    ↓
pipeline.py  (roda uma vez, antes da reunião de terça)
    ↓
Para cada uma das 8 áreas FM:
    ├── Spatial join → Caixinha 1 (Ocorrências) + Caixinha 4 (Cobertura)
    ├── LLM (Claude) → Caixinha 2 (Dinâmica Criminal)
    └── Filtro + Spatial join → Caixinha 3 (Fatores Urbanos)
    ↓
cache/
    ├── presidente_vargas.json
    ├── jardim_de_alah.json
    └── ... (8 arquivos)
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

**Por que ORCRIM está na Caixinha 2 e não numa caixinha própria?**
No relatório, ORCRIM aparece como um campo de identificação e é mencionado no texto de Dinâmica Criminal. Os RELINTs já descrevem a influência de facções. Faz mais sentido o spatial join de domínio territorial ser um input que enriquece a síntese do LLM do que uma caixinha separada.

**Por que PSR está na Caixinha 3 e não na Caixinha 2?**
PSR aparece na seção "Fatores de Incidência Criminal" do relatório — com responsável definido (SMAS) e tratado operacionalmente como um fator urbano a ser resolvido, não como elemento da dinâmica criminal.

**Por que o Disque Denúncia aparece em duas caixinhas?**
Porque o mesmo relato pode descrever um crime ocorrido (Caixinha 1) e o padrão de como ele ocorre (Caixinha 2). O LLM processa o texto uma vez e extrai as duas dimensões simultaneamente.
