# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O Projeto

Plataforma de inteligência criminal para o **CompStat Municipal da Prefeitura do Rio de Janeiro**, desenvolvida no Hackathon Anthropic 2026. O CompStat realiza reuniões semanais às terças-feiras presididas pelo Prefeito. O produto final é um **dashboard Streamlit** usado pelo analista na preparação da reunião, que gera automaticamente o **Relatório Analítico de Área** (impresso e distribuído na reunião).

O repositório de dados está em `../claude_impact_lab_compstat_rio/` — não está neste repo, mas é a fonte de tudo.

## Decisões de Arquitetura

Toda a documentação de decisões fica em `brainstorming/`. Leia antes de implementar qualquer coisa.

**`brainstorming/caixinhas-de-dados.md`** — decisão central do projeto: como os dados heterogêneos são normalizados em 4 estruturas por área antes de alimentar o dashboard.

## Arquitetura Planejada

### Pipeline (roda antes da reunião de terça)

`pipeline.py` processa todas as 8 áreas da FM e salva JSONs em `cache/`. Cada área gera 4 arquivos:

- `cache/{area}/ocorrencias.json` — contagens, distribuição temporal, heatmap points
- `cache/{area}/dinamica_criminal.json` — síntese LLM de RELINTs + Disque Denúncia + ORCRIM
- `cache/{area}/fatores_urbanos.json` — fatores por tipo e órgão responsável + PSR
- `cache/{area}/cobertura_operacional.json` — câmeras, polígono FM, pontos cegos

### Dashboard (Streamlit)

`dashboard.py` lê os JSONs do cache e não faz processamento pesado. O Claude API é chamado apenas no botão "Gerar Relatório", que preenche o template e exporta PDF/DOCX.

## Fontes de Dados

Todas em `../claude_impact_lab_compstat_rio/dados/`:

| Arquivo | Encoding | Separador | Nota |
|---|---|---|---|
| `df_ocorrencias_tratado - Extração 1 .csv` | utf-8 | `,` | 115k registros; `hora` e `dia_semana` têm 22 nulos |
| `disk_denuncia.csv` | latin1 | `;` | 83k linhas mas só 18k denúncias reais (JSON desnormalizado); deduplicar por `id_denuncia` |
| `fatores_urbanos.csv` | utf-8 | `,` | `subarea_nome` já mapeia para área FM |
| `cameras_areas_fm.csv` | utf-8 | `,` | `geometry` em WKT string; `nome_area_fm` já mapeado |

Shapefiles em `../claude_impact_lab_compstat_rio/sh_area_forca/` — 8 polígonos, campo `nome_subar`, encoding UTF-8.

RELINTs em `../claude_impact_lab_compstat_rio/relints/` — 8 DOCXs, um por área. Ler com `zipfile` + `xml.etree` (python-docx pode não estar disponível).

## Áreas da FM (8 áreas do dataset)

1. Rodoviária - Terminal Gentileza - Estação Leopoldina
2. Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria
3. Jardim de Alah
4. Campo Grande: Estação de Trem - Calçadão
5. Rio Sul
6. Praia de Botafogo - Rua Marquês de Abrantes
7. Estações São Francisco Xavier - Afonso Pena
8. Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia

## Pegadinhas Conhecidas

- **Disque Denúncia**: 65k linhas sem lat/long não são denúncias sem geolocalização — são linhas extras do JSON desnormalizado (órgãos, assuntos, envolvidos). As 18k denúncias reais quase todas têm lat/long.
- **Códigos de delito**: `15` = Roubo a transeunte, `16` = Roubo de celular, `19` = Roubo em coletivo.
- **Coordenadas dos fatores urbanos**: coluna `coordenada_x` é latitude, `coordenada_y` é longitude (nomenclatura invertida na fonte).
- **Shapefile encoding**: o DBF está em UTF-8, não latin1. Ler com `encoding='utf-8'`.
- **geopandas**: pode não estar no ambiente. Usar `shapely` diretamente para operações geoespaciais.
