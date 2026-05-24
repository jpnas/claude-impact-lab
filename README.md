# CompStat Rio — Plataforma de Inteligência Criminal

Plataforma de inteligência territorial desenvolvida para o **Hackathon Anthropic 2026**, em parceria com a **Secretaria-Geral do CompStat Municipal da Prefeitura do Rio de Janeiro**.

## O Problema

O CompStat Municipal opera sobre 22 áreas prioritárias de segurança pública na cidade do Rio. A cada ciclo semanal, a equipe precisa produzir um **Relatório Analítico de Área** por polígono — documento que subsidia diretamente as reuniões presididas pelo Prefeito.

O gargalo está na síntese: dados de ocorrências criminais georreferenciadas, denúncias qualitativas (Disque Denúncia), relatórios de inteligência de campo (RELINTs) e fatores urbanos (iluminação, vegetação, desordem urbana) vivem em silos separados. Cruzar essas camadas manualmente consome horas de trabalho — horas que deveriam estar sendo usadas em interpretação e tomada de decisão.

## A Solução

Uma plataforma baseada em IA (Claude) que:

1. **Ingere e normaliza** as 5 fontes de dados do CompStat (ocorrências lat/long, polígonos FM, fatores urbanos, Disque Denúncia, RELINTs)
2. **Cruza automaticamente** as camadas espaciais e qualitativas para identificar **coincidências de alto risco** — o "bingo" onde mancha criminal, fator urbano e dinâmica criminal se sobrepõem no mesmo trecho
3. **Sintetiza** a dinâmica criminal via LLM: modus operandi, rotas de fuga, pontos de receptação, influência de ORCRIMs
4. **Responde automaticamente** às 4 perguntas norteadoras das reuniões CompStat:
   - Qual deve ser a rota da FM?
   - Qual o horário de patrulhamento ideal?
   - Qual o modelo de emprego (moto, viatura, a pé)?
   - Como os órgãos devem resolver os fatores urbanos?
5. **Gera o Relatório Analítico de Área** completo — de horas de compilação manual para minutos

## Dados

Os dados utilizados estão no repositório de dados do projeto:
[`claude_impact_lab_compstat_rio`](https://github.com/jpnas/claude_impact_lab_compstat_rio)

Fontes:
- Ocorrências criminais com geolocalização (CSV)
- Polígonos de atuação da Força Municipal (Shapefile)
- Fatores urbanos de incidência criminal (CSV)
- Disque Denúncia (CSV)
- RELINTs da Força Municipal (DOCX)

## Stack

- **IA:** Claude API (Anthropic) — síntese qualitativa, geração de relatório, respostas às perguntas norteadoras
- **Geoespacial:** Python + GeoPandas + Shapely
- **Visualização:** Folium / Leaflet (heatmaps interativos)
- **Processamento de texto:** LLM pipeline para extração de entidades de documentos não estruturados

## Contexto

O CompStat Municipal do Rio é inspirado no modelo criado pelo NYPD nos anos 1990. Diferentemente das polícias estaduais, atua sobre a premissa de que **o ambiente urbano degradado é o facilitador estrutural da criminalidade oportunista** — e coordena órgãos municipais (Comlurb, RioLuz, SEOP, SMAS, Seconserva, CET-Rio) para resolver esses fatores de forma integrada e baseada em evidências.

---

Hackathon Anthropic 2026 | Prefeitura do Rio de Janeiro
