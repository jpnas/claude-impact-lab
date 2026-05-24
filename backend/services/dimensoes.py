import json
from backend.db import get_db


def get_dimensoes(slug: str) -> dict | None:
    db = get_db()
    row = db.execute(
        "SELECT id, nome, slug FROM areas WHERE slug = ?", (slug,)
    ).fetchone()
    if not row:
        return None
    area = dict(row)
    dims = db.execute(
        "SELECT tipo, dados, referencia_pipeline FROM dimensoes_analise WHERE area_id = ?",
        (area["id"],),
    ).fetchall()
    result: dict = {"area": area, "dimensoes": {}}
    for d in dims:
        result["dimensoes"][d["tipo"]] = {
            "dados": json.loads(d["dados"]),
            "referencia_pipeline": d["referencia_pipeline"],
        }
    return result


def list_areas() -> list[dict]:
    db = get_db()
    areas = db.execute("SELECT id, nome, slug FROM areas").fetchall()
    area_ids_with_cache = {
        row[0]
        for row in db.execute("SELECT DISTINCT area_id FROM dimensoes_analise").fetchall()
    }
    return [
        {**dict(a), "cache_disponivel": a["id"] in area_ids_with_cache}
        for a in areas
    ]
