import sqlite3
import json
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_PROJECT_ROOT = Path(__file__).parent.parent

_SCHEMA = """
CREATE TABLE IF NOT EXISTS areas (
    id   TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS reunioes (
    id           TEXT PRIMARY KEY,
    data_reuniao TEXT NOT NULL,
    criado_em    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS dimensoes_analise (
    id                  TEXT PRIMARY KEY,
    area_id             TEXT NOT NULL REFERENCES areas(id),
    tipo                TEXT NOT NULL CHECK (tipo IN (
        'ocorrencias','dinamica_criminal','fatores_urbanos',
        'cobertura_operacional','contexto_territorial','coincidencias'
    )),
    dados               TEXT NOT NULL,
    referencia_pipeline TEXT DEFAULT (datetime('now')),
    UNIQUE(area_id, tipo)
);

CREATE TABLE IF NOT EXISTS relatorios (
    id           TEXT PRIMARY KEY,
    area_id      TEXT NOT NULL REFERENCES areas(id),
    reuniao_id   TEXT REFERENCES reunioes(id),
    conteudo     TEXT,
    status       TEXT DEFAULT 'rascunho' CHECK (status IN ('rascunho','finalizado')),
    criado_em    TEXT DEFAULT (datetime('now')),
    atualizado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS mensagens_relatorio (
    id           TEXT PRIMARY KEY,
    relatorio_id TEXT NOT NULL REFERENCES relatorios(id),
    role         TEXT NOT NULL CHECK (role IN ('user','assistant')),
    conteudo     TEXT NOT NULL,
    criado_em    TEXT DEFAULT (datetime('now'))
);
"""

_AREAS = [
    ("Rodoviária - Terminal Gentileza - Estação Leopoldina", "rodoviaria"),
    ("Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria", "metro-botafogo"),
    ("Jardim de Alah", "jardim-de-alah"),
    ("Campo Grande: Estação de Trem - Calçadão", "campo-grande"),
    ("Rio Sul", "rio-sul"),
    ("Praia de Botafogo - Rua Marquês de Abrantes", "praia-botafogo"),
    ("Estações São Francisco Xavier - Afonso Pena", "estacoes-sfx"),
    ("Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia", "presidente-vargas"),
]

_conn: sqlite3.Connection | None = None


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    for nome, slug in _AREAS:
        conn.execute(
            "INSERT OR IGNORE INTO areas (id, nome, slug) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), nome, slug),
        )
    conn.commit()


def get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        db_path = Path(os.getenv("DB_PATH", str(_PROJECT_ROOT / "compstat.db")))
        _conn = sqlite3.connect(str(db_path), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _init_db(_conn)
    return _conn
