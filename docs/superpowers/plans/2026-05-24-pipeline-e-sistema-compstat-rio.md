# CompStat Rio — Pipeline + Backend + Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o sistema completo CompStat Rio: pipeline Python que processa dados heterogêneos em 6 dimensões por área FM, backend FastAPI que serve essas dimensões, e frontend Next.js com dashboard e geração de relatório via Claude API.

**Architecture:** O pipeline roda offline e persiste as 6 dimensões por área no Supabase. O backend FastAPI lê do Supabase e expõe endpoints REST + SSE para streaming do Claude. O frontend Next.js consome a API em dois modos: geração de relatório (pré-reunião) e dashboard da reunião.

**Tech Stack:** Python 3.11, FastAPI, shapely, anthropic, supabase-py, pandas, openpyxl; Next.js 14, TypeScript, TailwindCSS; Supabase (PostgreSQL + Storage).

**Data root:** `../claude_impact_lab_compstat_rio/`

**8 áreas FM (nome_subar no shapefile):**
1. `Rodoviária - Terminal Gentileza - Estação Leopoldina`
2. `Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria`
3. `Jardim de Alah`
4. `Campo Grande: Estação de Trem - Calçadão`
5. `Rio Sul`
6. `Praia de Botafogo - Rua Marquês de Abrantes`
7. `Estações São Francisco Xavier - Afonso Pena`
8. `Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia`

---

## File Map

```
claude-impact-lab/
├── pipeline/
│   ├── config.py                    # Paths, constants, Supabase env
│   ├── utils/
│   │   ├── shapefile.py             # Read .shp + .dbf sem geopandas
│   │   ├── geo.py                   # Point-in-polygon, geodesic distance
│   │   └── docx.py                  # Read DOCX via zipfile + xml.etree
│   ├── processadores/
│   │   ├── ocorrencias.py           # Fase 1 + Fase 2 enrich
│   │   ├── dinamica_criminal.py     # Fase 2 LLM
│   │   ├── fatores_urbanos.py       # Fase 1 + Fase 2 enrich
│   │   ├── cobertura_operacional.py # Fase 1
│   │   ├── contexto_territorial.py  # Fase 1
│   │   └── coincidencias.py         # Fase 3 LLM síntese
│   └── run_pipeline.py              # Orquestrador das 3 fases
├── backend/
│   ├── main.py                      # FastAPI app + CORS
│   ├── db.py                        # Supabase client singleton
│   ├── routers/
│   │   ├── areas.py                 # GET /areas, GET /areas/{slug}/dimensoes
│   │   └── relatorios.py            # POST gerar, POST chat, GET, PUT relatorio
│   └── services/
│       ├── dimensoes.py             # Lê dimensoes_analise do Supabase
│       └── relatorio.py             # Claude API streaming SSE
├── frontend/                        # Next.js app (npx create-next-app)
│   ├── src/app/
│   │   ├── page.tsx                 # Seleção de área
│   │   ├── areas/[slug]/
│   │   │   ├── relatorio/page.tsx   # Chat + artifact (Modo 1)
│   │   │   └── dashboard/page.tsx   # Dashboard (Modo 2)
│   │   └── layout.tsx
│   ├── src/components/
│   │   ├── AreaSelector.tsx
│   │   ├── RelatorioChatPanel.tsx
│   │   ├── RelatorioArtifact.tsx
│   │   ├── DashboardHeatmap.tsx
│   │   └── DimensaoCard.tsx
│   └── src/lib/
│       └── api.ts                   # Fetch wrapper para o backend
└── supabase/
    └── schema.sql                   # DDL das 5 tabelas
```

---

## Task 1: Ambiente e Dependências

**Files:**
- Create: `pipeline/requirements.txt`
- Create: `backend/requirements.txt`
- Create: `.env.example`

- [ ] **Step 1: Instalar pacotes Python do pipeline**

```bash
pip install shapely anthropic supabase-py pyshp
```

Verificar: `python3 -c "import shapely, anthropic, supabase; print('ok')"` → deve imprimir `ok`

- [ ] **Step 2: Criar `pipeline/requirements.txt`**

```
shapely>=2.0
anthropic>=0.25
supabase>=2.0
pyshp>=2.3
pandas>=1.5
openpyxl>=3.0
numpy>=1.24
```

- [ ] **Step 3: Criar `backend/requirements.txt`**

```
fastapi>=0.111
uvicorn[standard]>=0.29
anthropic>=0.25
supabase>=2.0
httpx>=0.27
python-dotenv>=1.0
```

- [ ] **Step 4: Criar `.env.example`**

```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
DATA_ROOT=../claude_impact_lab_compstat_rio
```

- [ ] **Step 5: Criar `.env` local com valores reais** (não comitar)

Copiar `.env.example` → `.env` e preencher com as credenciais reais.

- [ ] **Step 6: Commit**

```bash
git add pipeline/requirements.txt backend/requirements.txt .env.example
git commit -m "chore: add Python requirements and env template"
```

---

## Task 2: Schema Supabase

**Files:**
- Create: `supabase/schema.sql`

- [ ] **Step 1: Criar `supabase/schema.sql`**

```sql
create extension if not exists "uuid-ossp";

create table if not exists areas (
  id uuid primary key default uuid_generate_v4(),
  nome text not null,
  slug text not null unique
);

create table if not exists reunioes (
  id uuid primary key default uuid_generate_v4(),
  data_reuniao date not null,
  criado_em timestamp default now()
);

create table if not exists dimensoes_analise (
  id uuid primary key default uuid_generate_v4(),
  area_id uuid not null references areas(id),
  tipo text not null check (tipo in (
    'ocorrencias','dinamica_criminal','fatores_urbanos',
    'cobertura_operacional','contexto_territorial','coincidencias'
  )),
  dados jsonb not null,
  referencia_pipeline timestamp default now()
);

create table if not exists relatorios (
  id uuid primary key default uuid_generate_v4(),
  area_id uuid not null references areas(id),
  reuniao_id uuid references reunioes(id),
  conteudo text,
  status text default 'rascunho' check (status in ('rascunho','finalizado')),
  criado_em timestamp default now(),
  atualizado_em timestamp default now()
);

create table if not exists mensagens_relatorio (
  id uuid primary key default uuid_generate_v4(),
  relatorio_id uuid not null references relatorios(id),
  role text not null check (role in ('user','assistant')),
  conteudo text not null,
  criado_em timestamp default now()
);

-- Seed das 8 áreas FM
insert into areas (nome, slug) values
  ('Rodoviária - Terminal Gentileza - Estação Leopoldina', 'rodoviaria'),
  ('Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria', 'metro-botafogo'),
  ('Jardim de Alah', 'jardim-de-alah'),
  ('Campo Grande: Estação de Trem - Calçadão', 'campo-grande'),
  ('Rio Sul', 'rio-sul'),
  ('Praia de Botafogo - Rua Marquês de Abrantes', 'praia-botafogo'),
  ('Estações São Francisco Xavier - Afonso Pena', 'estacoes-sfx'),
  ('Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia', 'presidente-vargas')
on conflict (slug) do nothing;
```

- [ ] **Step 2: Executar no Supabase SQL Editor**

Acessar o dashboard Supabase → SQL Editor → colar e executar `schema.sql`.

Verificar: todas as 5 tabelas criadas, 8 rows em `areas`.

- [ ] **Step 3: Commit**

```bash
git add supabase/schema.sql
git commit -m "feat: add Supabase schema with 5 tables and area seed"
```

---

## Task 3: Utilitários do Pipeline

**Files:**
- Create: `pipeline/__init__.py`
- Create: `pipeline/config.py`
- Create: `pipeline/utils/__init__.py`
- Create: `pipeline/utils/shapefile.py`
- Create: `pipeline/utils/geo.py`
- Create: `pipeline/utils/docx.py`

- [ ] **Step 1: Criar `pipeline/config.py`**

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATA_ROOT = Path(os.getenv("DATA_ROOT", "../claude_impact_lab_compstat_rio"))
DADOS = DATA_ROOT / "dados"
RELINTS = DATA_ROOT / "relints"
SHAPEFILE = DATA_ROOT / "sh_area_forca" / "areas_forca_municipal"
OUTROS = DADOS / "outros dados"

OCORRENCIAS_CSV = DADOS / "df_ocorrencias_tratado - Extração 1 .csv"
DISK_DENUNCIA_CSV = DADOS / "disk_denuncia.csv"
FATORES_CSV = DADOS / "fatores_urbanos.csv"
CAMERAS_CSV = DADOS / "cameras_areas_fm.csv"
DOMINIO_CSV = OUTROS / "dominio_territorial - Extração 1.csv"
PSR_XLSX = OUTROS / "CPSR_2020_2022_2024.xlsx"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

RAIO_METROS = 100
DD_CLASSES_CRIMINAIS = {
    "CRIMES CONTRA O PATRIMÔNIO",
    "SUBSTÂNCIAS ENTORPECENTES",
    "ARMAS DE FOGO E ARTEFATOS EXPLOSIVOS",
}
DD_TOP_N = 40
JANELA_MESES = 12
```

- [ ] **Step 2: Criar `pipeline/utils/shapefile.py`**

```python
import struct
import shapely.geometry as sg
from pathlib import Path


def _read_dbf(dbf_path: Path) -> list[dict]:
    with open(dbf_path, "rb") as f:
        header = f.read(32)
        num_records = struct.unpack("<I", header[4:8])[0]
        header_size = struct.unpack("<H", header[8:10])[0]
        record_size = struct.unpack("<H", header[10:12])[0]
        field_data = f.read(header_size - 32 - 1)
        f.read(1)  # terminator
        fields = []
        for i in range(0, len(field_data), 32):
            chunk = field_data[i : i + 32]
            if len(chunk) < 32:
                break
            name = chunk[:11].replace(b"\x00", b"").decode("utf-8", errors="replace")
            typ = chr(chunk[11])
            length = chunk[16]
            fields.append((name, typ, length))
        records = []
        for _ in range(num_records):
            raw = f.read(record_size)
            vals = {}
            offset = 1
            for name, typ, length in fields:
                vals[name] = raw[offset : offset + length].decode("utf-8", errors="replace").strip()
                offset += length
            records.append(vals)
    return records


def _read_shp_polygons(shp_path: Path) -> list[sg.Polygon]:
    """Read polygon geometries from .shp file (shape type 5 = Polygon)."""
    import shapefile as sf
    reader = sf.Reader(str(shp_path))
    polygons = []
    for shape in reader.shapes():
        if shape.shapeType == 5:
            # shapefile lib gives parts + points
            parts = list(shape.parts) + [len(shape.points)]
            rings = []
            for i in range(len(parts) - 1):
                ring = shape.points[parts[i] : parts[i + 1]]
                rings.append(ring)
            if rings:
                exterior = rings[0]
                holes = rings[1:]
                polygons.append(sg.Polygon(exterior, holes))
            else:
                polygons.append(sg.Polygon())
        else:
            polygons.append(sg.Polygon())
    return polygons


def load_areas(shapefile_base: Path) -> dict[str, sg.Polygon]:
    """Returns {nome_subar: Polygon} for all 8 FM areas."""
    records = _read_dbf(Path(str(shapefile_base) + ".dbf"))
    polygons = _read_shp_polygons(Path(str(shapefile_base) + ".shp"))
    return {rec["nome_subar"]: poly for rec, poly in zip(records, polygons)}
```

- [ ] **Step 3: Criar `pipeline/utils/geo.py`**

```python
import math
import shapely.geometry as sg


def point_in_polygon(lat: float, lon: float, polygon: sg.Polygon) -> bool:
    return polygon.contains(sg.Point(lon, lat))


def geodesic_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in metres."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def points_within_radius(
    center_lat: float,
    center_lon: float,
    points: list[tuple[float, float]],
    radius_m: float,
) -> list[tuple[float, float]]:
    """Return subset of (lat, lon) points within radius_m of center."""
    return [
        p for p in points
        if geodesic_distance_m(center_lat, center_lon, p[0], p[1]) <= radius_m
    ]
```

- [ ] **Step 4: Criar `pipeline/utils/docx.py`**

```python
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def read_docx_text(path: Path) -> str:
    """Extract plain text from a DOCX file without python-docx."""
    with zipfile.ZipFile(path) as zf:
        with zf.open("word/document.xml") as f:
            tree = ET.parse(f)
    root = tree.getroot()
    paras = []
    for p in root.iter(f"{{{_W}}}p"):
        texts = [t.text or "" for t in p.iter(f"{{{_W}}}t")]
        paras.append("".join(texts))
    return "\n".join(paras)
```

- [ ] **Step 5: Criar `pipeline/__init__.py` e `pipeline/utils/__init__.py`** (vazios)

```bash
touch pipeline/__init__.py pipeline/utils/__init__.py pipeline/processadores/__init__.py
```

- [ ] **Step 6: Testar utils**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
areas = load_areas(SHAPEFILE)
print(list(areas.keys()))
assert len(areas) == 8
print('shapefile ok')
"
```

Esperado: lista com 8 nomes de área + `shapefile ok`

```bash
python3 -c "
from pipeline.utils.geo import geodesic_distance_m
d = geodesic_distance_m(-22.909, -43.180, -22.910, -43.181)
assert 100 < d < 200, f'unexpected distance: {d}'
print(f'distance ok: {d:.1f}m')
"
```

- [ ] **Step 7: Commit**

```bash
git add pipeline/
git commit -m "feat: pipeline utils — shapefile reader, geo distance, docx reader"
```

---

## Task 4: Processador — Ocorrências (Fase 1)

**Files:**
- Create: `pipeline/processadores/ocorrencias.py`

**Lógica:** Lê `df_ocorrencias_tratado.csv`, filtra por spatial join com polígono FM, janela de 12 meses móveis, agrega por tipo/hora/dia/logradouro, calcula YoY vs 12 meses anteriores.

- [ ] **Step 1: Criar `pipeline/processadores/ocorrencias.py`**

```python
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from pathlib import Path
import shapely.geometry as sg

from pipeline.config import OCORRENCIAS_CSV, JANELA_MESES
from pipeline.utils.geo import point_in_polygon


def _load_ocorrencias() -> pd.DataFrame:
    df = pd.read_csv(OCORRENCIAS_CSV, encoding="utf-8", low_memory=False)
    df["data_fato"] = pd.to_datetime(df["data_fato"], errors="coerce")
    return df.dropna(subset=["data_fato"])


def _spatial_filter(df: pd.DataFrame, polygon: sg.Polygon) -> pd.DataFrame:
    mask = df.apply(
        lambda r: point_in_polygon(r["latitude"], r["longitude"], polygon)
        if pd.notna(r.get("latitude")) and pd.notna(r.get("longitude"))
        else False,
        axis=1,
    )
    return df[mask]


def build_ocorrencias_base(polygon: sg.Polygon, ref_date: date | None = None) -> dict:
    if ref_date is None:
        ref_date = date.today()
    df = _load_ocorrencias()
    df_area = _spatial_filter(df, polygon)

    cutoff_end = pd.Timestamp(ref_date)
    cutoff_start = cutoff_end - pd.DateOffset(months=JANELA_MESES)
    cutoff_prev_start = cutoff_start - pd.DateOffset(months=JANELA_MESES)

    periodo = df_area[(df_area["data_fato"] >= cutoff_start) & (df_area["data_fato"] < cutoff_end)]
    prev = df_area[(df_area["data_fato"] >= cutoff_prev_start) & (df_area["data_fato"] < cutoff_start)]

    total = len(periodo)
    total_prev = len(prev)
    if total_prev > 0:
        variacao = f"{round((total - total_prev) / total_prev * 100):+d}%"
    else:
        variacao = "N/A"

    por_tipo = periodo["descricao_delito"].value_counts().head(10).to_dict()
    por_hora = (
        periodo["hora"].dropna().astype(int).astype(str).str.zfill(2)
        .value_counts().to_dict()
    )
    por_dia = periodo["dia_semana"].dropna().value_counts().to_dict()

    top_locf = periodo["locf"].dropna().value_counts().head(10)

    heatmap_points = []
    for _, row in periodo.dropna(subset=["latitude", "longitude"]).iterrows():
        heatmap_points.append([round(row["latitude"], 4), round(row["longitude"], 4), 1.0])

    hora_critica = max(por_hora, key=por_hora.get) + "h" if por_hora else None
    dia_critico = max(por_dia, key=por_dia.get) if por_dia else None

    return {
        "total_periodo": total,
        "variacao_yoy": variacao,
        "periodo_referencia": f"{cutoff_start.strftime('%Y-%m')} a {cutoff_end.strftime('%Y-%m')}",
        "por_tipo": por_tipo,
        "por_hora": por_hora,
        "por_dia_semana": por_dia,
        "hora_critica": hora_critica,
        "dia_critico": dia_critico,
        "top_logradouros": [
            {"nome": nome, "contagem": int(cnt)} for nome, cnt in top_locf.items()
        ],
        "heatmap_points": heatmap_points[:500],  # cap for Supabase JSON size
    }
```

- [ ] **Step 2: Testar com área Presidente Vargas**

```python
# test_ocorrencias.py (rodar uma vez, não precisa de pytest aqui)
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
from pipeline.processadores.ocorrencias import build_ocorrencias_base

areas = load_areas(SHAPEFILE)
polygon = areas["Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia"]
result = build_ocorrencias_base(polygon)
print(f"Total: {result['total_periodo']}")
print(f"Variação YoY: {result['variacao_yoy']}")
print(f"Top tipos: {list(result['por_tipo'].keys())[:3]}")
print(f"Top logradouros: {result['top_logradouros'][:2]}")
assert result["total_periodo"] > 0
print("ocorrencias ok")
```

```bash
python3 -c "exec(open('test_ocorrencias.py').read())"
```

Esperado: total > 0, variação no formato `+12%`, top logradouros com dicts `{nome, contagem}`.

- [ ] **Step 3: Commit**

```bash
git add pipeline/processadores/ocorrencias.py
git commit -m "feat: ocorrencias processor — spatial filter, 12-month window, YoY"
```

---

## Task 5: Processador — Fatores Urbanos (Fase 1)

**Files:**
- Create: `pipeline/processadores/fatores_urbanos.py`

**Pegadinha:** `coordenada_x` = latitude, `coordenada_y` = longitude.

- [ ] **Step 1: Criar `pipeline/processadores/fatores_urbanos.py`**

```python
from __future__ import annotations
import pandas as pd
import shapely.geometry as sg

from pipeline.config import FATORES_CSV
from pipeline.utils.geo import point_in_polygon


def _load_fatores() -> pd.DataFrame:
    df = pd.read_csv(FATORES_CSV, encoding="utf-8", low_memory=False)
    # coordenada_x = lat, coordenada_y = lon (invertido na fonte)
    df = df.rename(columns={"coordenada_x": "latitude", "coordenada_y": "longitude"})
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    return df.dropna(subset=["latitude", "longitude"])


def build_fatores_urbanos_base(area_nome: str, polygon: sg.Polygon) -> dict:
    df = _load_fatores()
    # First try subarea_nome filter (fast), then fall back to spatial join
    df_area = df[df["subarea_nome"] == area_nome]
    if df_area.empty:
        df_area = df[df.apply(
            lambda r: point_in_polygon(r["latitude"], r["longitude"], polygon), axis=1
        )]

    fatores = []
    por_orgao: dict[str, int] = {}
    for (tipo, orgao), grp in df_area.groupby(
        ["tipo_ocorrencia_descricao", "orgao_responsavel"], dropna=False
    ):
        pontos = [
            [round(r["latitude"], 4), round(r["longitude"], 4)]
            for _, r in grp.iterrows()
        ]
        cnt = len(grp)
        fatores.append({
            "tipo": str(tipo),
            "orgao_responsavel": str(orgao),
            "contagem": cnt,
            "pontos": pontos,
        })
        por_orgao[str(orgao)] = por_orgao.get(str(orgao), 0) + cnt

    fatores.sort(key=lambda x: x["contagem"], reverse=True)

    return {
        "fatores": fatores,
        "por_orgao": por_orgao,
        "fatores_adicionais_relint": [],  # preenchido na Fase 2
    }
```

- [ ] **Step 2: Testar**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
from pipeline.processadores.fatores_urbanos import build_fatores_urbanos_base

areas = load_areas(SHAPEFILE)
nome = 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'
result = build_fatores_urbanos_base(nome, areas[nome])
print(f'Fatores: {len(result[\"fatores\"])}')
print(f'Órgãos: {result[\"por_orgao\"]}')
assert len(result['fatores']) > 0
print('fatores_urbanos ok')
"
```

- [ ] **Step 3: Commit**

```bash
git add pipeline/processadores/fatores_urbanos.py
git commit -m "feat: fatores_urbanos processor — subarea filter + spatial fallback"
```

---

## Task 6: Processador — Cobertura Operacional (Fase 1)

**Files:**
- Create: `pipeline/processadores/cobertura_operacional.py`

**Pegadinha:** câmeras têm `geometry` em WKT `POINT(lon lat)` (lon primeiro). Pontos cegos: logradouros acima do P80 de crimes sem câmera em raio 100m.

- [ ] **Step 1: Criar `pipeline/processadores/cobertura_operacional.py`**

```python
from __future__ import annotations
import pandas as pd
import numpy as np
import re
import shapely.geometry as sg
import shapely.wkt

from pipeline.config import CAMERAS_CSV, OCORRENCIAS_CSV, RAIO_METROS, JANELA_MESES
from pipeline.utils.geo import geodesic_distance_m, point_in_polygon


def _parse_wkt_point(wkt: str) -> tuple[float, float] | None:
    """Returns (lat, lon) from WKT POINT(lon lat)."""
    try:
        geom = shapely.wkt.loads(wkt)
        return geom.y, geom.x  # lat, lon
    except Exception:
        return None


def _load_cameras(area_nome: str) -> list[dict]:
    df = pd.read_csv(CAMERAS_CSV, encoding="utf-8")
    df_area = df[df["nome_area_fm"] == area_nome]
    cameras = []
    for _, row in df_area.iterrows():
        parsed = _parse_wkt_point(str(row.get("geometry", "")))
        if parsed:
            cameras.append({"id": str(row["id_ponto"]), "lat": parsed[0], "lon": parsed[1]})
    return cameras


def _top_logradouros_brutos(polygon: sg.Polygon) -> pd.Series:
    """Load raw ocorrencias, filter by polygon, return logradouro counts (P80+)."""
    df = pd.read_csv(OCORRENCIAS_CSV, encoding="utf-8", low_memory=False, usecols=["locf", "latitude", "longitude", "data_fato"])
    df["data_fato"] = pd.to_datetime(df["data_fato"], errors="coerce")
    cutoff = pd.Timestamp.today() - pd.DateOffset(months=JANELA_MESES)
    df = df[df["data_fato"] >= cutoff]
    mask = df.apply(
        lambda r: point_in_polygon(r["latitude"], r["longitude"], polygon)
        if pd.notna(r.get("latitude")) and pd.notna(r.get("longitude")) else False,
        axis=1,
    )
    df_area = df[mask]
    counts = df_area["locf"].dropna().value_counts()
    p80 = np.percentile(counts.values, 80) if len(counts) > 0 else 0
    return counts[counts >= p80]


def build_cobertura_operacional(area_nome: str, polygon: sg.Polygon) -> dict:
    cameras = _load_cameras(area_nome)
    cam_coords = [(c["lat"], c["lon"]) for c in cameras]
    top_locf = _top_logradouros_brutos(polygon)

    # Approximate lat/lon per logradouro from ocorrencias data (centroid of crimes)
    df = pd.read_csv(OCORRENCIAS_CSV, encoding="utf-8", low_memory=False, usecols=["locf", "latitude", "longitude"])
    df = df.dropna(subset=["latitude", "longitude"])

    pontos_cegos = []
    for locf, cnt in top_locf.items():
        group = df[df["locf"] == locf]
        if group.empty:
            continue
        clat = group["latitude"].mean()
        clon = group["longitude"].mean()
        nearby = [
            c for c in cam_coords
            if geodesic_distance_m(clat, clon, c[0], c[1]) <= RAIO_METROS
        ]
        if len(nearby) == 0:
            pontos_cegos.append({
                "logradouro": locf,
                "contagem_crimes": int(cnt),
                "cameras_proximas": 0,
            })

    poly_geom = sg.mapping(polygon)

    return {
        "poligono": poly_geom,
        "cameras": cameras,
        "total_cameras": len(cameras),
        "pontos_cegos": sorted(pontos_cegos, key=lambda x: x["contagem_crimes"], reverse=True),
    }
```

- [ ] **Step 2: Testar**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
from pipeline.processadores.cobertura_operacional import build_cobertura_operacional

areas = load_areas(SHAPEFILE)
nome = 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'
result = build_cobertura_operacional(nome, areas[nome])
print(f'Câmeras: {result[\"total_cameras\"]}')
print(f'Pontos cegos: {len(result[\"pontos_cegos\"])}')
print(result['pontos_cegos'][:2])
print('cobertura_operacional ok')
"
```

- [ ] **Step 3: Commit**

```bash
git add pipeline/processadores/cobertura_operacional.py
git commit -m "feat: cobertura_operacional — camera spatial check, blind spot detection"
```

---

## Task 7: Processador — Contexto Territorial (Fase 1)

**Files:**
- Create: `pipeline/processadores/contexto_territorial.py`

**Fontes:** `dominio_territorial.csv` (WKT polígonos) e `CPSR_2020_2022_2024.xlsx` (PSR).

- [ ] **Step 1: Criar `pipeline/processadores/contexto_territorial.py`**

```python
from __future__ import annotations
import pandas as pd
import shapely.wkt
import shapely.geometry as sg

from pipeline.config import DOMINIO_CSV, PSR_XLSX
from pipeline.utils.geo import point_in_polygon


def _load_dominio() -> pd.DataFrame:
    df = pd.read_csv(DOMINIO_CSV, encoding="utf-8", low_memory=False)
    return df


def _load_psr() -> pd.DataFrame:
    df = pd.read_excel(PSR_XLSX, engine="openpyxl")
    return df


def build_contexto_territorial(polygon: sg.Polygon) -> dict:
    # --- Domínio territorial ---
    df_dom = _load_dominio()
    # Expect columns: geometry (WKT), orcrim (or similar), area_km2 or compute from intersection
    # Detect ORCRIM column
    orcrim_col = next(
        (c for c in df_dom.columns if "orcrim" in c.lower() or "organiz" in c.lower()),
        None,
    )
    geom_col = next(
        (c for c in df_dom.columns if "geom" in c.lower() or "wkt" in c.lower() or "polygon" in c.lower()),
        df_dom.columns[0],
    )

    orcrim_areas: dict[str, float] = {}
    for _, row in df_dom.iterrows():
        try:
            geom = shapely.wkt.loads(str(row[geom_col]))
            intersection = polygon.intersection(geom)
            if intersection.is_empty:
                continue
            area = intersection.area
            orcrim = str(row[orcrim_col]) if orcrim_col else "Desconhecido"
            orcrim_areas[orcrim] = orcrim_areas.get(orcrim, 0) + area
        except Exception:
            continue

    total_area = sum(orcrim_areas.values()) or 1.0
    orcrim_proporcional = {k: round(v / total_area, 3) for k, v in orcrim_areas.items()}
    orcrim_dominante = max(orcrim_proporcional, key=orcrim_proporcional.get) if orcrim_proporcional else "N/A"

    # --- PSR ---
    df_psr = _load_psr()
    lat_col = next((c for c in df_psr.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df_psr.columns if "lon" in c.lower() or "lng" in c.lower()), None)
    ano_col = next((c for c in df_psr.columns if "ano" in c.lower() or "year" in c.lower()), None)

    psr_data: dict[str, int] = {}
    psr_points: list[list[float]] = []
    if lat_col and lon_col and ano_col:
        df_psr[lat_col] = pd.to_numeric(df_psr[lat_col], errors="coerce")
        df_psr[lon_col] = pd.to_numeric(df_psr[lon_col], errors="coerce")
        df_psr_valid = df_psr.dropna(subset=[lat_col, lon_col])
        df_psr_area = df_psr_valid[df_psr_valid.apply(
            lambda r: point_in_polygon(r[lat_col], r[lon_col], polygon), axis=1
        )]
        for ano in [2020, 2022, 2024]:
            cnt = len(df_psr_area[df_psr_area[ano_col] == ano])
            if cnt > 0:
                psr_data[f"total_{ano}"] = cnt
        for _, row in df_psr_area.iterrows():
            psr_points.append([round(row[lat_col], 4), round(row[lon_col], 4)])

    totais = [psr_data.get(f"total_{a}", 0) for a in [2020, 2022, 2024]]
    if totais[-1] > totais[0]:
        tendencia = "crescente"
    elif totais[-1] < totais[0]:
        tendencia = "decrescente"
    else:
        tendencia = "estável"

    return {
        "orcrim_dominante": orcrim_dominante,
        "orcrim_por_tipo": orcrim_proporcional,
        "comunidades_proximas": [],  # não há fonte estruturada; pode ser enriquecido
        "psr": {**psr_data, "tendencia": tendencia, "pontos": psr_points[:200]},
    }
```

- [ ] **Step 2: Inspecionar colunas reais do CSV e ajustar se necessário**

```bash
python3 -c "
import pandas as pd
df = pd.read_csv('../claude_impact_lab_compstat_rio/dados/outros dados/dominio_territorial - Extração 1.csv', encoding='utf-8', nrows=3)
print(df.columns.tolist())
print(df.head(2))
"
```

Se colunas forem diferentes das esperadas (`geom_col`, `orcrim_col`), ajustar os `next(...)` em `build_contexto_territorial`.

```bash
python3 -c "
import pandas as pd
df = pd.read_excel('../claude_impact_lab_compstat_rio/dados/outros dados/CPSR_2020_2022_2024.xlsx', engine='openpyxl', nrows=3)
print(df.columns.tolist())
print(df.head(2))
"
```

- [ ] **Step 3: Testar**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
from pipeline.processadores.contexto_territorial import build_contexto_territorial

areas = load_areas(SHAPEFILE)
nome = 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'
result = build_contexto_territorial(areas[nome])
print(f'ORCRIM dominante: {result[\"orcrim_dominante\"]}')
print(f'PSR: {result[\"psr\"]}')
print('contexto_territorial ok')
"
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/processadores/contexto_territorial.py
git commit -m "feat: contexto_territorial — ORCRIM spatial proportion + PSR census"
```

---

## Task 8: Processadores LLM — Fase 2 (Dinâmica Criminal + Enriquecimento)

**Files:**
- Create: `pipeline/processadores/dinamica_criminal.py`

**Lógica:** LLM recebe RELINT + top 40 Disque Denúncia (deduplicado, 3 classes, mais recentes). ORCRIM dominante do Contexto Territorial como background.

- [ ] **Step 1: Criar `pipeline/processadores/dinamica_criminal.py`**

```python
from __future__ import annotations
import pandas as pd
import anthropic
import json
import shapely.geometry as sg
from pathlib import Path

from pipeline.config import (
    RELINTS, DISK_DENUNCIA_CSV, ANTHROPIC_API_KEY,
    DD_CLASSES_CRIMINAIS, DD_TOP_N, RAIO_METROS,
)
from pipeline.utils.docx import read_docx_text
from pipeline.utils.geo import point_in_polygon


def _find_relint(area_nome: str) -> Path | None:
    for f in RELINTS.glob("*.docx"):
        return f  # crude: pick first matching — refine by area mapping if needed
    return None


_AREA_TO_RELINT_KEYWORD = {
    "Rodoviária - Terminal Gentileza - Estação Leopoldina": "Rodoviaria",
    "Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria": "Metro_Botafogo",
    "Jardim de Alah": "Jardim_de_Alah",
    "Campo Grande: Estação de Trem - Calçadão": "Campo_Grande",
    "Rio Sul": "Rio_Sul",
    "Praia de Botafogo - Rua Marquês de Abrantes": "Praia_Botafogo",
    "Estações São Francisco Xavier - Afonso Pena": "Estacoes_SFX",
    "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia": "Presidente_Vargas",
}


def _find_relint_for_area(area_nome: str) -> Path | None:
    keyword = _AREA_TO_RELINT_KEYWORD.get(area_nome, "")
    for f in RELINTS.glob("*.docx"):
        if keyword.lower() in f.name.lower():
            return f
    return None


def _load_top_dd(polygon: sg.Polygon) -> list[str]:
    df = pd.read_csv(DISK_DENUNCIA_CSV, encoding="latin1", sep=";", low_memory=False)
    df = df.drop_duplicates(subset=["id_denuncia"])
    df = df[df["assuntos.classe"].isin(DD_CLASSES_CRIMINAIS)]
    df["latitude"] = df["latitude"].astype(str).str.replace(",", ".").pipe(pd.to_numeric, errors="coerce")
    df["longitude"] = df["longitude"].astype(str).str.replace(",", ".").pipe(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])
    df_area = df[df.apply(
        lambda r: point_in_polygon(r["latitude"], r["longitude"], polygon), axis=1
    )]
    df_area = df_area.sort_values("data_denuncia", ascending=False).head(DD_TOP_N)
    return df_area["relato_redacted"].fillna("").tolist()


def build_dinamica_criminal(area_nome: str, polygon: sg.Polygon, orcrim_dominante: str) -> dict:
    relint_path = _find_relint_for_area(area_nome)
    relint_text = read_docx_text(relint_path) if relint_path else "(RELINT não disponível)"
    relatos = _load_top_dd(polygon)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Você é um analista de inteligência criminal. Analise o Relatório de Inteligência (RELINT) e os relatos do Disque Denúncia para a área FM "{area_nome}".

**Contexto:** A organização criminosa dominante na área é {orcrim_dominante}.

**RELINT:**
{relint_text[:8000]}

**Top {len(relatos)} relatos Disque Denúncia (mais recentes):**
{chr(10).join(f'- {r}' for r in relatos[:DD_TOP_N])}

Retorne um JSON com exatamente estas chaves:
{{
  "modalidade_predominante": "string",
  "modus_operandi": "string",
  "rotas_de_fuga": ["string"],
  "pontos_de_receptacao": ["string"],
  "perfil_suspeitos": "string",
  "orcrim_influencia": "string",
  "narrativa_completa": "parágrafo de 3-5 frases"
}}

Retorne APENAS o JSON, sem markdown."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def enrich_ocorrencias_dd(base: dict, polygon: sg.Polygon) -> dict:
    """Enrich ocorrencias with DD signal (Fase 2)."""
    relatos = _load_top_dd(polygon)
    if not relatos:
        return base

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Analise estes {len(relatos)} relatos do Disque Denúncia e extraia padrões criminais não capturados pelas ocorrências registradas. Retorne JSON:
{{
  "sinais_dd": ["padrão 1", "padrão 2"],
  "locais_suspeitos_mencionados": ["local 1", "local 2"]
}}

Relatos:
{chr(10).join(f'- {r}' for r in relatos)}

Retorne APENAS o JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    extra = json.loads(text)
    return {**base, **extra}


def enrich_fatores_relint(base: dict, area_nome: str) -> dict:
    """Enrich fatores_urbanos with RELINT signals (Fase 2)."""
    relint_path = _find_relint_for_area(area_nome)
    if not relint_path:
        return base

    relint_text = read_docx_text(relint_path)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Do seguinte RELINT, extraia fatores urbanos que facilitam crimes mas não estão nos dados estruturados de campo (ex: horários de feiras, locais sem iluminação mencionados narrativamente).

RELINT:
{relint_text[:6000]}

Retorne JSON:
{{"fatores_adicionais_relint": ["fator 1", "fator 2"]}}

Retorne APENAS o JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    extra = json.loads(text)
    return {**base, **extra}
```

- [ ] **Step 2: Testar (requer ANTHROPIC_API_KEY no .env)**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
from pipeline.processadores.dinamica_criminal import build_dinamica_criminal

areas = load_areas(SHAPEFILE)
nome = 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'
result = build_dinamica_criminal(nome, areas[nome], 'TCP')
print(result.keys())
assert 'modalidade_predominante' in result
print('dinamica_criminal ok')
"
```

- [ ] **Step 3: Commit**

```bash
git add pipeline/processadores/dinamica_criminal.py
git commit -m "feat: dinamica_criminal LLM processor — RELINT + Disque Denuncia synthesis"
```

---

## Task 9: Processador — Coincidências (Fase 3)

**Files:**
- Create: `pipeline/processadores/coincidencias.py`

**Algoritmo:** (1) cruzamento espacial determinístico: top logradouros + fatores ≤100m + ponto cego; (2) LLM avalia relevância causal e gera recomendações.

- [ ] **Step 1: Criar `pipeline/processadores/coincidencias.py`**

```python
from __future__ import annotations
import json
import anthropic
import shapely.geometry as sg

from pipeline.config import ANTHROPIC_API_KEY, RAIO_METROS
from pipeline.utils.geo import geodesic_distance_m


def _score(crimes: int, max_crimes: int, n_fatores: int, max_fatores: int, ponto_cego: bool) -> float:
    crime_norm = crimes / max_crimes if max_crimes > 0 else 0
    fator_norm = n_fatores / max_fatores if max_fatores > 0 else 0
    return round(crime_norm * 0.5 + fator_norm * 0.3 + (0.2 if ponto_cego else 0), 3)


def _centroid_for_logradouro(logradouro: str, heatmap_points: list) -> tuple[float, float] | None:
    """Rough centroid from heatmap (lat, lon pairs)."""
    # heatmap_points is [[lat, lon, weight], ...]
    if not heatmap_points:
        return None
    lats = [p[0] for p in heatmap_points]
    lons = [p[1] for p in heatmap_points]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def build_coincidencias(
    ocorrencias: dict,
    fatores_urbanos: dict,
    cobertura_operacional: dict,
    dinamica_criminal: dict,
    contexto_territorial: dict,
) -> dict:
    top_locf = ocorrencias.get("top_logradouros", [])
    fatores = fatores_urbanos.get("fatores", [])
    pontos_cegos_set = {p["logradouro"] for p in cobertura_operacional.get("pontos_cegos", [])}
    heatmap = ocorrencias.get("heatmap_points", [])

    # Etapa 1: cruzamento espacial determinístico
    trechos = []
    for locf_obj in top_locf:
        locf = locf_obj["nome"]
        crimes = locf_obj["contagem"]
        # Use heatmap centroid as proxy for logradouro position
        centroid = _centroid_for_logradouro(locf, heatmap)
        fatores_proximos = []
        if centroid:
            for fator in fatores:
                for ponto in fator.get("pontos", []):
                    if len(ponto) >= 2 and geodesic_distance_m(centroid[0], centroid[1], ponto[0], ponto[1]) <= RAIO_METROS:
                        fatores_proximos.append(fator["tipo"])
                        break
        fatores_proximos = list(set(fatores_proximos))
        ponto_cego = locf in pontos_cegos_set
        trechos.append({
            "logradouro": locf,
            "crimes_no_periodo": crimes,
            "ponto_cego": ponto_cego,
            "fatores_proximos": fatores_proximos,
        })

    max_crimes = max((t["crimes_no_periodo"] for t in trechos), default=1)
    max_fatores = max((len(t["fatores_proximos"]) for t in trechos), default=1)

    # Etapa 2: LLM avalia relevância causal
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""Você é um analista de segurança pública. Avalie a relevância causal dos fatores urbanos nos trechos críticos da área.

**Perfil criminal:**
- Modalidade: {dinamica_criminal.get('modalidade_predominante', '')}
- Horário predominante: {ocorrencias.get('hora_critica', '')}
- Dia crítico: {ocorrencias.get('dia_critico', '')}
- ORCRIM: {contexto_territorial.get('orcrim_dominante', '')}

**Trechos para avaliar:**
{json.dumps(trechos, ensure_ascii=False, indent=2)}

Para cada trecho, retorne:
1. Quais fatores são causalmente relevantes para o padrão de crime identificado (ex: iluminação só é relevante se pico for noturno)
2. Uma justificativa operacional (1-2 frases)

Também retorne recomendações operacionais.

Retorne JSON:
{{
  "trechos_avaliados": [
    {{
      "logradouro": "string",
      "fatores_relevantes": [{{"tipo": "string", "orgao": "string", "relevancia": "string"}}],
      "justificativa": "string"
    }}
  ],
  "recomendacoes": {{
    "rota_fm": "string",
    "horario_patrulhamento": "string",
    "modelo_emprego": "string",
    "acoes_municipais": [{{"orgao": "string", "acao": "string"}}]
  }}
}}

Retorne APENAS o JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    llm_result = json.loads(text)

    # Merge LLM avaliação with deterministic scores
    avaliados = {t["logradouro"]: t for t in llm_result.get("trechos_avaliados", [])}
    trechos_criticos = []
    for trecho in trechos:
        avaliado = avaliados.get(trecho["logradouro"], {})
        fatores_relevantes = avaliado.get("fatores_relevantes", [])
        score = _score(
            trecho["crimes_no_periodo"], max_crimes,
            len(fatores_relevantes), max_fatores,
            trecho["ponto_cego"],
        )
        trechos_criticos.append({
            "logradouro": trecho["logradouro"],
            "score_prioridade": score,
            "crimes_no_periodo": trecho["crimes_no_periodo"],
            "ponto_cego": trecho["ponto_cego"],
            "fatores_relevantes": fatores_relevantes,
            "justificativa": avaliado.get("justificativa", ""),
        })

    trechos_criticos.sort(key=lambda x: x["score_prioridade"], reverse=True)

    return {
        "trechos_criticos": trechos_criticos,
        "recomendacoes": llm_result.get("recomendacoes", {}),
    }
```

- [ ] **Step 2: Testar (integração das 5 dimensões anteriores)**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
from pipeline.processadores.ocorrencias import build_ocorrencias_base
from pipeline.processadores.fatores_urbanos import build_fatores_urbanos_base
from pipeline.processadores.cobertura_operacional import build_cobertura_operacional
from pipeline.processadores.contexto_territorial import build_contexto_territorial
from pipeline.processadores.coincidencias import build_coincidencias

areas = load_areas(SHAPEFILE)
nome = 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'
poly = areas[nome]

oc = build_ocorrencias_base(poly)
fat = build_fatores_urbanos_base(nome, poly)
cob = build_cobertura_operacional(nome, poly)
ctx = build_contexto_territorial(poly)

from pipeline.processadores.dinamica_criminal import build_dinamica_criminal
din = build_dinamica_criminal(nome, poly, ctx['orcrim_dominante'])

result = build_coincidencias(oc, fat, cob, din, ctx)
print(f'Trechos críticos: {len(result[\"trechos_criticos\"])}')
print(result['trechos_criticos'][:1])
print('coincidencias ok')
"
```

- [ ] **Step 3: Commit**

```bash
git add pipeline/processadores/coincidencias.py
git commit -m "feat: coincidencias processor — spatial cross + LLM causal evaluation"
```

---

## Task 10: Orquestrador do Pipeline + Persistência Supabase

**Files:**
- Create: `pipeline/run_pipeline.py`

**Lógica:** Descobre áreas via shapefile, roda Fase 1 para todas, Fase 2 em paralelo (asyncio), Fase 3 sequencial. Persiste cada dimensão no Supabase.

- [ ] **Step 1: Criar `pipeline/run_pipeline.py`**

```python
from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from supabase import create_client, Client

from pipeline.config import SHAPEFILE, SUPABASE_URL, SUPABASE_SERVICE_KEY
from pipeline.utils.shapefile import load_areas
from pipeline.processadores.ocorrencias import build_ocorrencias_base
from pipeline.processadores.fatores_urbanos import build_fatores_urbanos_base
from pipeline.processadores.cobertura_operacional import build_cobertura_operacional
from pipeline.processadores.contexto_territorial import build_contexto_territorial
from pipeline.processadores.dinamica_criminal import (
    build_dinamica_criminal, enrich_ocorrencias_dd, enrich_fatores_relint
)
from pipeline.processadores.coincidencias import build_coincidencias

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_area_id(sb: Client, nome: str) -> str | None:
    res = sb.table("areas").select("id").eq("nome", nome).execute()
    if res.data:
        return res.data[0]["id"]
    return None


def upsert_dimensao(sb: Client, area_id: str, tipo: str, dados: dict) -> None:
    sb.table("dimensoes_analise").upsert({
        "area_id": area_id,
        "tipo": tipo,
        "dados": dados,
        "referencia_pipeline": datetime.utcnow().isoformat(),
    }, on_conflict="area_id,tipo").execute()
    log.info(f"  ✓ {tipo}")


def process_area(sb: Client, area_nome: str, polygon) -> None:
    log.info(f"=== {area_nome} ===")
    area_id = get_area_id(sb, area_nome)
    if not area_id:
        log.warning(f"  área não encontrada no Supabase: {area_nome}")
        return

    # Fase 1
    log.info("  Fase 1: determinística...")
    oc_base = build_ocorrencias_base(polygon)
    fat_base = build_fatores_urbanos_base(area_nome, polygon)
    cob = build_cobertura_operacional(area_nome, polygon)
    ctx = build_contexto_territorial(polygon)

    upsert_dimensao(sb, area_id, "cobertura_operacional", cob)
    upsert_dimensao(sb, area_id, "contexto_territorial", ctx)

    # Fase 2 (LLM)
    log.info("  Fase 2: LLM enrichment...")
    oc_final = enrich_ocorrencias_dd(oc_base, polygon)
    fat_final = enrich_fatores_relint(fat_base, area_nome)
    din = build_dinamica_criminal(area_nome, polygon, ctx["orcrim_dominante"])

    upsert_dimensao(sb, area_id, "ocorrencias", oc_final)
    upsert_dimensao(sb, area_id, "fatores_urbanos", fat_final)
    upsert_dimensao(sb, area_id, "dinamica_criminal", din)

    # Fase 3
    log.info("  Fase 3: síntese...")
    coin = build_coincidencias(oc_final, fat_final, cob, din, ctx)
    upsert_dimensao(sb, area_id, "coincidencias", coin)

    log.info(f"  Área concluída.")


def main():
    areas = load_areas(SHAPEFILE)
    sb = get_supabase()
    log.info(f"Iniciando pipeline para {len(areas)} áreas")
    for nome, polygon in areas.items():
        try:
            process_area(sb, nome, polygon)
        except Exception as e:
            log.error(f"Erro na área {nome}: {e}", exc_info=True)
    log.info("Pipeline concluído.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Testar dry-run com uma área (sem Supabase)**

```bash
python3 -c "
from pipeline.utils.shapefile import load_areas
from pipeline.config import SHAPEFILE
areas = load_areas(SHAPEFILE)
print('Areas disponíveis:', list(areas.keys()))
print(f'Total: {len(areas)}')
"
```

- [ ] **Step 3: Executar pipeline completo para uma área**

```bash
python3 -c "
from supabase import create_client
from pipeline.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, SHAPEFILE
from pipeline.utils.shapefile import load_areas
from pipeline.run_pipeline import process_area, get_supabase

areas = load_areas(SHAPEFILE)
nome = 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'
sb = get_supabase()
process_area(sb, nome, areas[nome])
print('Uma área processada com sucesso')
"
```

Verificar no Supabase: 6 rows em `dimensoes_analise` para a área Presidente Vargas.

- [ ] **Step 4: Executar pipeline completo para todas as áreas**

```bash
python3 pipeline/run_pipeline.py
```

Esperado: log com 8 áreas, cada uma com 6 dimensões persistidas.

- [ ] **Step 5: Commit**

```bash
git add pipeline/run_pipeline.py
git commit -m "feat: pipeline orchestrator — 3 phases, all areas, Supabase persistence"
```

---

## Task 11: Backend FastAPI

**Files:**
- Create: `backend/main.py`
- Create: `backend/db.py`
- Create: `backend/routers/areas.py`
- Create: `backend/routers/relatorios.py`
- Create: `backend/services/dimensoes.py`
- Create: `backend/services/relatorio.py`

- [ ] **Step 1: Criar `backend/db.py`**

```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client
```

- [ ] **Step 2: Criar `backend/services/dimensoes.py`**

```python
from backend.db import get_db


def get_dimensoes(slug: str) -> dict:
    db = get_db()
    area = db.table("areas").select("id,nome,slug").eq("slug", slug).single().execute()
    if not area.data:
        return None
    area_id = area.data["id"]
    dims = db.table("dimensoes_analise").select("tipo,dados,referencia_pipeline").eq("area_id", area_id).execute()
    result = {"area": area.data, "dimensoes": {}}
    for row in dims.data:
        result["dimensoes"][row["tipo"]] = {
            "dados": row["dados"],
            "referencia_pipeline": row["referencia_pipeline"],
        }
    return result


def list_areas() -> list[dict]:
    db = get_db()
    areas = db.table("areas").select("id,nome,slug").execute()
    # Add cache status
    dims = db.table("dimensoes_analise").select("area_id").execute()
    area_ids_with_cache = {row["area_id"] for row in dims.data}
    result = []
    for area in areas.data:
        result.append({**area, "cache_disponivel": area["id"] in area_ids_with_cache})
    return result
```

- [ ] **Step 3: Criar `backend/services/relatorio.py`**

```python
from __future__ import annotations
import anthropic
import os
from backend.db import get_db
from backend.services.dimensoes import get_dimensoes
import json


def _build_system_prompt(dimensoes: dict) -> str:
    area = dimensoes["area"]["nome"]
    dims = dimensoes["dimensoes"]
    return f"""Você é um analista de segurança pública do CompStat Municipal do Rio de Janeiro.
Você tem acesso às seguintes dimensões de análise da área FM "{area}":

**Ocorrências:** {json.dumps(dims.get('ocorrencias', {}).get('dados', {}), ensure_ascii=False)[:3000]}

**Dinâmica Criminal:** {json.dumps(dims.get('dinamica_criminal', {}).get('dados', {}), ensure_ascii=False)[:2000]}

**Fatores Urbanos:** {json.dumps(dims.get('fatores_urbanos', {}).get('dados', {}), ensure_ascii=False)[:1500]}

**Cobertura Operacional:** {json.dumps(dims.get('cobertura_operacional', {}).get('dados', {}), ensure_ascii=False)[:1500]}

**Contexto Territorial:** {json.dumps(dims.get('contexto_territorial', {}).get('dados', {}), ensure_ascii=False)[:1000]}

**Coincidências e Recomendações:** {json.dumps(dims.get('coincidencias', {}).get('dados', {}), ensure_ascii=False)[:2000]}

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
        yield "data: {\"error\": \"Área não encontrada\"}\n\n"
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

    msgs_res = db.table("mensagens_relatorio").select("role,conteudo").eq("relatorio_id", relatorio_id).order("criado_em").execute()
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

    # Persist messages
    db.table("mensagens_relatorio").insert({"relatorio_id": relatorio_id, "role": "user", "conteudo": user_message}).execute()
    db.table("mensagens_relatorio").insert({"relatorio_id": relatorio_id, "role": "assistant", "conteudo": full_response}).execute()
    yield "data: [DONE]\n\n"
```

- [ ] **Step 4: Criar `backend/routers/areas.py`**

```python
from fastapi import APIRouter, HTTPException
from backend.services.dimensoes import get_dimensoes, list_areas

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("")
def get_areas():
    return list_areas()


@router.get("/{slug}/dimensoes")
def get_area_dimensoes(slug: str):
    result = get_dimensoes(slug)
    if not result:
        raise HTTPException(404, "Área não encontrada")
    return result
```

- [ ] **Step 5: Criar `backend/routers/relatorios.py`**

```python
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.db import get_db
from backend.services.relatorio import stream_relatorio, stream_chat

router = APIRouter(prefix="/areas", tags=["relatorios"])


class ChatBody(BaseModel):
    relatorio_id: str
    mensagem: str


class SalvarBody(BaseModel):
    reuniao_id: str | None = None
    conteudo: str
    status: str = "finalizado"


@router.post("/{slug}/relatorio/gerar")
async def gerar_relatorio(slug: str):
    return StreamingResponse(stream_relatorio(slug), media_type="text/event-stream")


@router.post("/{slug}/relatorio/chat")
async def chat_relatorio(slug: str, body: ChatBody):
    return StreamingResponse(
        stream_chat(slug, body.relatorio_id, body.mensagem),
        media_type="text/event-stream",
    )


@router.get("/{slug}/relatorio")
def get_relatorio(slug: str, reuniao_id: str | None = None):
    db = get_db()
    area = db.table("areas").select("id").eq("slug", slug).single().execute()
    if not area.data:
        raise HTTPException(404, "Área não encontrada")
    query = db.table("relatorios").select("*").eq("area_id", area.data["id"])
    if reuniao_id:
        query = query.eq("reuniao_id", reuniao_id)
    res = query.order("criado_em", desc=True).limit(1).execute()
    if not res.data:
        raise HTTPException(404, "Relatório não encontrado")
    return res.data[0]


@router.put("/{slug}/relatorio")
def salvar_relatorio(slug: str, body: SalvarBody):
    db = get_db()
    area = db.table("areas").select("id").eq("slug", slug).single().execute()
    if not area.data:
        raise HTTPException(404, "Área não encontrada")
    res = db.table("relatorios").insert({
        "area_id": area.data["id"],
        "reuniao_id": body.reuniao_id,
        "conteudo": body.conteudo,
        "status": body.status,
    }).execute()
    return res.data[0]
```

- [ ] **Step 6: Criar `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import areas, relatorios

app = FastAPI(title="CompStat Rio API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(areas.router)
app.include_router(relatorios.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Criar `backend/__init__.py` e `backend/routers/__init__.py` e `backend/services/__init__.py`**

```bash
touch backend/__init__.py backend/routers/__init__.py backend/services/__init__.py
```

- [ ] **Step 8: Testar o backend**

```bash
cd /Users/joaopedronascimento/claude-impact-lab
uvicorn backend.main:app --reload --port 8000
```

Em outro terminal:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/areas
curl http://localhost:8000/areas/presidente-vargas/dimensoes | python3 -m json.tool | head -30
```

Esperado: `{"status": "ok"}`, lista de 8 áreas, dimensões JSON.

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: FastAPI backend — 6 endpoints, SSE streaming, Supabase integration"
```

---

## Task 12: Frontend Next.js — Setup e Seleção de Área

**Files:**
- Create: `frontend/` (Next.js app)
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/AreaSelector.tsx`

- [ ] **Step 1: Criar app Next.js**

```bash
cd /Users/joaopedronascimento/claude-impact-lab
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --no-import-alias
```

Aceitar defaults. Então mover `src/` para `frontend/src/` (já configurado pelo next).

- [ ] **Step 2: Criar `frontend/src/lib/api.ts`**

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Area {
  id: string;
  nome: string;
  slug: string;
  cache_disponivel: boolean;
}

export interface Dimensoes {
  area: Area;
  dimensoes: Record<string, { dados: unknown; referencia_pipeline: string }>;
}

export async function fetchAreas(): Promise<Area[]> {
  const res = await fetch(`${API_BASE}/areas`);
  if (!res.ok) throw new Error("Erro ao buscar áreas");
  return res.json();
}

export async function fetchDimensoes(slug: string): Promise<Dimensoes> {
  const res = await fetch(`${API_BASE}/areas/${slug}/dimensoes`);
  if (!res.ok) throw new Error("Área não encontrada");
  return res.json();
}

export async function fetchRelatorio(slug: string, reuniaoId?: string) {
  const url = reuniaoId
    ? `${API_BASE}/areas/${slug}/relatorio?reuniao_id=${reuniaoId}`
    : `${API_BASE}/areas/${slug}/relatorio`;
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Erro ao buscar relatório");
  return res.json();
}

export async function salvarRelatorio(slug: string, conteudo: string, reuniaoId?: string) {
  const res = await fetch(`${API_BASE}/areas/${slug}/relatorio`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conteudo, reuniao_id: reuniaoId, status: "finalizado" }),
  });
  if (!res.ok) throw new Error("Erro ao salvar relatório");
  return res.json();
}

export function streamRelatorio(
  slug: string,
  onChunk: (text: string) => void,
  onDone: () => void,
): () => void {
  const controller = new AbortController();
  fetch(`${API_BASE}/areas/${slug}/relatorio/gerar`, {
    method: "POST",
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") { onDone(); return; }
        const { text } = JSON.parse(payload);
        if (text) onChunk(text);
      }
    }
  });
  return () => controller.abort();
}

export function streamChat(
  slug: string,
  relatorioId: string,
  mensagem: string,
  onChunk: (text: string) => void,
  onDone: () => void,
): () => void {
  const controller = new AbortController();
  fetch(`${API_BASE}/areas/${slug}/relatorio/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ relatorio_id: relatorioId, mensagem }),
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") { onDone(); return; }
        const { text } = JSON.parse(payload);
        if (text) onChunk(text);
      }
    }
  });
  return () => controller.abort();
}
```

- [ ] **Step 3: Criar `frontend/src/components/AreaSelector.tsx`**

```typescript
"use client";
import { Area } from "@/lib/api";
import Link from "next/link";

export function AreaSelector({ areas }: { areas: Area[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
      {areas.map((area) => (
        <div
          key={area.slug}
          className={`rounded-lg border p-5 ${
            area.cache_disponivel
              ? "border-blue-500 bg-blue-50 hover:bg-blue-100"
              : "border-gray-200 bg-gray-50 opacity-60"
          }`}
        >
          <h2 className="font-semibold text-gray-900 text-sm mb-3">{area.nome}</h2>
          <div className="flex gap-2">
            {area.cache_disponivel ? (
              <>
                <Link
                  href={`/areas/${area.slug}/relatorio`}
                  className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Gerar Relatório
                </Link>
                <Link
                  href={`/areas/${area.slug}/dashboard`}
                  className="text-xs px-3 py-1.5 border border-blue-600 text-blue-600 rounded hover:bg-blue-50"
                >
                  Dashboard
                </Link>
              </>
            ) : (
              <span className="text-xs text-gray-400">Pipeline não executado</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Criar `frontend/src/app/page.tsx`**

```typescript
import { fetchAreas } from "@/lib/api";
import { AreaSelector } from "@/components/AreaSelector";

export const revalidate = 60;

export default async function Home() {
  const areas = await fetchAreas();

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-bold text-gray-900">CompStat Rio</h1>
          <p className="text-sm text-gray-500">Plataforma de Inteligência Criminal — Força Municipal</p>
        </div>
      </header>
      <div className="max-w-4xl mx-auto px-6 py-10">
        <h2 className="text-lg font-semibold text-gray-700 mb-6">Selecione a Área FM</h2>
        <AreaSelector areas={areas} />
      </div>
    </main>
  );
}
```

- [ ] **Step 5: Adicionar `.env.local` no frontend**

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
```

- [ ] **Step 6: Testar homepage**

```bash
cd frontend && npm run dev
```

Abrir `http://localhost:3000` — deve mostrar 8 cards de área, com botões "Gerar Relatório" e "Dashboard" para as que têm cache.

- [ ] **Step 7: Commit**

```bash
cd ..
git add frontend/src/app/page.tsx frontend/src/components/AreaSelector.tsx frontend/src/lib/api.ts
git commit -m "feat: Next.js homepage — area selector with cache status"
```

---

## Task 13: Frontend — Página de Relatório (Modo 1)

**Files:**
- Create: `frontend/src/app/areas/[slug]/relatorio/page.tsx`
- Create: `frontend/src/components/RelatorioChatPanel.tsx`
- Create: `frontend/src/components/RelatorioArtifact.tsx`

- [ ] **Step 1: Criar `frontend/src/components/RelatorioArtifact.tsx`**

```typescript
"use client";
import ReactMarkdown from "react-markdown";

interface Props {
  conteudo: string;
  streaming: boolean;
  onSalvar: () => void;
}

export function RelatorioArtifact({ conteudo, streaming, onSalvar }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b bg-white">
        <span className="text-sm font-medium text-gray-700">
          Relatório Analítico {streaming && <span className="text-blue-500 animate-pulse">●</span>}
        </span>
        {!streaming && conteudo && (
          <button
            onClick={onSalvar}
            className="text-xs px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Salvar Relatório
          </button>
        )}
      </div>
      <div className="flex-1 overflow-auto p-6 prose prose-sm max-w-none">
        {conteudo ? (
          <ReactMarkdown>{conteudo}</ReactMarkdown>
        ) : (
          <p className="text-gray-400 text-sm">O relatório será gerado aqui...</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Instalar react-markdown**

```bash
cd frontend && npm install react-markdown
```

- [ ] **Step 3: Criar `frontend/src/components/RelatorioChatPanel.tsx`**

```typescript
"use client";
import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  slug: string;
  relatorioId: string | null;
  onStreamChunk: (text: string) => void;
  onStreamDone: () => void;
  onGerar: () => void;
  streaming: boolean;
}

export function RelatorioChatPanel({
  slug, relatorioId, onStreamChunk, onStreamDone, onGerar, streaming,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [chatStreaming, setChatStreaming] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const sendMessage = async () => {
    if (!input.trim() || !relatorioId || chatStreaming) return;
    const userMsg = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setChatStreaming(true);
    let assistantContent = "";

    const res = await fetch(`http://localhost:8000/areas/${slug}/relatorio/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ relatorio_id: relatorioId, mensagem: userMsg }),
    });
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") { setChatStreaming(false); break; }
        const { text } = JSON.parse(payload);
        if (text) {
          assistantContent += text;
          onStreamChunk(text);
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: assistantContent };
            return updated;
          });
        }
      }
    }
  };

  return (
    <div className="flex flex-col h-full border-r bg-gray-50">
      <div className="px-4 py-3 border-b bg-white">
        <h2 className="text-sm font-semibold text-gray-700">Chat com o Analista</h2>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-xs text-gray-400">Gere o relatório e depois refine via chat.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`text-sm p-2 rounded ${m.role === "user" ? "bg-blue-100 ml-4" : "bg-white border mr-4"}`}>
            {m.content}
          </div>
        ))}
      </div>
      <div className="p-3 border-t bg-white space-y-2">
        {!relatorioId && (
          <button
            onClick={onGerar}
            disabled={streaming}
            className="w-full py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {streaming ? "Gerando..." : "Gerar Relatório"}
          </button>
        )}
        {relatorioId && (
          <div className="flex gap-2">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ajuste o relatório..."
              className="flex-1 text-sm border rounded px-3 py-1.5"
              disabled={chatStreaming}
            />
            <button
              onClick={sendMessage}
              disabled={chatStreaming || !input.trim()}
              className="text-sm px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Enviar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Criar `frontend/src/app/areas/[slug]/relatorio/page.tsx`**

```typescript
"use client";
import { useState, useCallback } from "react";
import { RelatorioChatPanel } from "@/components/RelatorioChatPanel";
import { RelatorioArtifact } from "@/components/RelatorioArtifact";
import { salvarRelatorio } from "@/lib/api";
import Link from "next/link";

export default function RelatorioPage({ params }: { params: { slug: string } }) {
  const { slug } = params;
  const [conteudo, setConteudo] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [relatorioId, setRelatorioId] = useState<string | null>(null);

  const handleGerar = useCallback(async () => {
    setConteudo("");
    setStreaming(true);
    const res = await fetch(`http://localhost:8000/areas/${slug}/relatorio/gerar`, { method: "POST" });
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const lines = decoder.decode(value).split("\n");
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") { setStreaming(false); break; }
        const { text } = JSON.parse(payload);
        if (text) { full += text; setConteudo((c) => c + text); }
      }
    }
  }, [slug]);

  const handleSalvar = useCallback(async () => {
    const saved = await salvarRelatorio(slug, conteudo);
    setRelatorioId(saved.id);
    alert("Relatório salvo!");
  }, [slug, conteudo]);

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center gap-4 px-4 py-2 border-b bg-white">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">← Áreas</Link>
        <h1 className="text-sm font-semibold text-gray-900 flex-1">{slug} — Relatório</h1>
        <Link href={`/areas/${slug}/dashboard`} className="text-sm text-blue-600 hover:underline">
          Ver Dashboard →
        </Link>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-72 flex-shrink-0">
          <RelatorioChatPanel
            slug={slug}
            relatorioId={relatorioId}
            onStreamChunk={(t) => setConteudo((c) => c + t)}
            onStreamDone={() => setStreaming(false)}
            onGerar={handleGerar}
            streaming={streaming}
          />
        </div>
        <div className="flex-1 overflow-hidden">
          <RelatorioArtifact conteudo={conteudo} streaming={streaming} onSalvar={handleSalvar} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Testar Modo 1**

Com backend rodando em :8000 e frontend em :3000, acessar `http://localhost:3000/areas/presidente-vargas/relatorio`.

Clicar "Gerar Relatório" → deve aparecer streaming de texto no painel direito. Clicar "Salvar Relatório" → alert de confirmação.

- [ ] **Step 6: Commit**

```bash
cd ..
git add frontend/src/app/areas/ frontend/src/components/RelatorioChatPanel.tsx frontend/src/components/RelatorioArtifact.tsx
git commit -m "feat: relatorio page — streaming generation + multi-turn chat (Modo 1)"
```

---

## Task 14: Frontend — Dashboard da Reunião (Modo 2)

**Files:**
- Create: `frontend/src/app/areas/[slug]/dashboard/page.tsx`
- Create: `frontend/src/components/DimensaoCard.tsx`

- [ ] **Step 1: Criar `frontend/src/components/DimensaoCard.tsx`**

```typescript
interface Props {
  titulo: string;
  children: React.ReactNode;
}

export function DimensaoCard({ titulo, children }: Props) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{titulo}</h3>
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Criar `frontend/src/app/areas/[slug]/dashboard/page.tsx`**

```typescript
import { fetchDimensoes, fetchRelatorio } from "@/lib/api";
import { DimensaoCard } from "@/components/DimensaoCard";
import Link from "next/link";
import { notFound } from "next/navigation";

export const revalidate = 300;

export default async function DashboardPage({ params }: { params: { slug: string } }) {
  const { slug } = params;

  let dimensoes, relatorio;
  try {
    dimensoes = await fetchDimensoes(slug);
  } catch {
    notFound();
  }
  relatorio = await fetchRelatorio(slug);

  const oc = dimensoes.dimensoes.ocorrencias?.dados as any;
  const din = dimensoes.dimensoes.dinamica_criminal?.dados as any;
  const cob = dimensoes.dimensoes.cobertura_operacional?.dados as any;
  const ctx = dimensoes.dimensoes.contexto_territorial?.dados as any;
  const coin = dimensoes.dimensoes.coincidencias?.dados as any;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-6 py-3 flex items-center gap-4">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">← Áreas</Link>
        <h1 className="text-sm font-bold text-gray-900 flex-1">{dimensoes.area.nome}</h1>
        <Link href={`/areas/${slug}/relatorio`} className="text-sm text-blue-600 hover:underline">
          Gerar Relatório →
        </Link>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Ocorrências */}
        {oc && (
          <DimensaoCard titulo="Ocorrências">
            <p className="text-3xl font-bold text-gray-900">{oc.total_periodo}</p>
            <p className="text-sm text-gray-500">
              {oc.variacao_yoy} vs. ano anterior · {oc.periodo_referencia}
            </p>
            <div className="mt-3 space-y-1">
              {Object.entries(oc.por_tipo || {}).slice(0, 5).map(([tipo, cnt]) => (
                <div key={tipo} className="flex justify-between text-xs text-gray-600">
                  <span>{tipo}</span><span className="font-medium">{cnt as number}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Pico: {oc.hora_critica} · {oc.dia_critico}</p>
          </DimensaoCard>
        )}

        {/* Contexto Territorial */}
        {ctx && (
          <DimensaoCard titulo="Contexto Territorial">
            <p className="text-lg font-bold text-red-600">{ctx.orcrim_dominante}</p>
            <div className="mt-2 space-y-1">
              {Object.entries(ctx.orcrim_por_tipo || {}).map(([org, pct]) => (
                <div key={org} className="flex justify-between text-xs text-gray-600">
                  <span>{org}</span>
                  <span className="font-medium">{((pct as number) * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
            {ctx.psr && (
              <div className="mt-3 text-xs text-gray-500">
                PSR 2024: {ctx.psr.total_2024 ?? 0} · tendência {ctx.psr.tendencia}
              </div>
            )}
          </DimensaoCard>
        )}

        {/* Cobertura Operacional */}
        {cob && (
          <DimensaoCard titulo="Cobertura Operacional">
            <p className="text-2xl font-bold">{cob.total_cameras} <span className="text-sm font-normal text-gray-500">câmeras</span></p>
            <p className="text-sm text-red-500 mt-1">{cob.pontos_cegos?.length ?? 0} pontos cegos</p>
            <div className="mt-3 space-y-1">
              {(cob.pontos_cegos || []).slice(0, 3).map((pc: any) => (
                <div key={pc.logradouro} className="text-xs text-gray-600">
                  {pc.logradouro} ({pc.contagem_crimes} crimes)
                </div>
              ))}
            </div>
          </DimensaoCard>
        )}

        {/* Dinâmica Criminal */}
        {din && (
          <DimensaoCard titulo="Dinâmica Criminal">
            <p className="text-sm font-semibold text-gray-800">{din.modalidade_predominante}</p>
            <p className="text-xs text-gray-500 mt-1">{din.modus_operandi}</p>
            <p className="text-xs text-gray-500 mt-2">Suspeitos: {din.perfil_suspeitos}</p>
          </DimensaoCard>
        )}

        {/* Trechos Críticos */}
        {coin && (
          <div className="md:col-span-2">
            <DimensaoCard titulo="Trechos Críticos">
              <div className="space-y-3">
                {(coin.trechos_criticos || []).slice(0, 5).map((t: any) => (
                  <div key={t.logradouro} className="border-l-4 pl-3 border-orange-400">
                    <div className="flex justify-between items-start">
                      <p className="text-sm font-medium text-gray-800">{t.logradouro}</p>
                      <span className="text-xs font-bold text-orange-600 ml-2">
                        {(t.score_prioridade * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{t.justificativa}</p>
                    {t.ponto_cego && (
                      <span className="text-xs text-red-500">⚠ Ponto cego</span>
                    )}
                  </div>
                ))}
              </div>
              {coin.recomendacoes && (
                <div className="mt-4 p-3 bg-blue-50 rounded text-xs text-blue-800">
                  <strong>Rota FM:</strong> {coin.recomendacoes.rota_fm}<br />
                  <strong>Horário:</strong> {coin.recomendacoes.horario_patrulhamento} ·{" "}
                  <strong>Modelo:</strong> {coin.recomendacoes.modelo_emprego}
                </div>
              )}
            </DimensaoCard>
          </div>
        )}

        {/* Relatório Salvo */}
        {relatorio && (
          <div className="md:col-span-3">
            <DimensaoCard titulo="Relatório Analítico">
              <div className="prose prose-sm max-w-none text-gray-700 max-h-64 overflow-auto">
                <pre className="whitespace-pre-wrap text-xs">{relatorio.conteudo}</pre>
              </div>
            </DimensaoCard>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Testar Dashboard**

Com backend em :8000 e pipeline já executado, acessar `http://localhost:3000/areas/presidente-vargas/dashboard`.

Verificar: cards de Ocorrências, Contexto Territorial, Cobertura Operacional, Dinâmica Criminal, Trechos Críticos aparecem com dados reais.

- [ ] **Step 4: Commit**

```bash
cd ..
git add frontend/src/app/areas/ frontend/src/components/DimensaoCard.tsx
git commit -m "feat: dashboard page — 6 dimensoes visualization, Modo 2 complete"
```

---

## Self-Review vs. Spec

### Spec coverage:

| Requisito do Spec | Task |
|---|---|
| 6 dimensões por área | Tasks 4-9 |
| Fase 1 determinística | Tasks 4-7 |
| Fase 2 LLM paralelo | Task 8 |
| Fase 3 síntese | Task 9 |
| Persiste no Supabase | Task 10 |
| Schema Supabase (5 tabelas) | Task 2 |
| GET /areas | Task 11 |
| GET /areas/{slug}/dimensoes | Task 11 |
| POST /relatorio/gerar (SSE) | Task 11 |
| POST /relatorio/chat (SSE) | Task 11 |
| GET e PUT /relatorio | Task 11 |
| Frontend / (seleção de área) | Task 12 |
| Frontend Modo 1 (relatório) | Task 13 |
| Frontend Modo 2 (dashboard) | Task 14 |
| Janela 12 meses móveis | Task 4 |
| YoY % | Task 4 |
| Raio 100m pontos cegos | Task 6 |
| Raio 100m coincidências | Task 9 |
| Filtro DD: deduplicar + 3 classes + top 40 | Task 8 |
| lat/lon DD: replace(',','.') | Task 8 |
| WKT câmeras: shapely.wkt.loads | Task 6 |
| Shapefile: UTF-8, nome_subar | Task 3 |
| DOCX: zipfile + xml.etree | Task 3 |
| PSR: openpyxl | Task 7 |
| score_prioridade fórmula | Task 9 |
| coordenada_x=lat, coordenada_y=lon | Task 5 |
| Data-driven (não hardcoded) | Task 3 (load_areas) |

### Gaps identificados:
- **Mapa heatmap** no dashboard: spec menciona `heatmap_points` mas Task 14 não renderiza o mapa. Isso exigiria Leaflet ou similar — deixado para iteração após MVP.
- **Autenticação**: spec diz "nenhuma — acesso único", alinhado com o plano.
- **Fase 2 paralela entre áreas**: `run_pipeline.py` roda sequencialmente por simplicidade. Pode adicionar `asyncio.gather` após MVP validado.

---
