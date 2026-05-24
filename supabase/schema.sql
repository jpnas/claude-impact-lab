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

-- Unique index on dimensoes_analise for upsert
create unique index if not exists dimensoes_analise_area_tipo_idx on dimensoes_analise(area_id, tipo);

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
