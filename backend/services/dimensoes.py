from backend.db import get_db


def get_dimensoes(slug: str) -> dict | None:
    db = get_db()
    res = db.table("areas").select("id,nome,slug").eq("slug", slug).execute()
    if not res.data:
        return None
    area = res.data[0]
    area_id = area["id"]
    dims = db.table("dimensoes_analise").select("tipo,dados,referencia_pipeline").eq("area_id", area_id).execute()
    result = {"area": area, "dimensoes": {}}
    for row in dims.data:
        result["dimensoes"][row["tipo"]] = {
            "dados": row["dados"],
            "referencia_pipeline": row["referencia_pipeline"],
        }
    return result


def list_areas() -> list[dict]:
    db = get_db()
    areas_res = db.table("areas").select("id,nome,slug").execute()
    dims_res = db.table("dimensoes_analise").select("area_id").execute()
    area_ids_with_cache = {row["area_id"] for row in dims_res.data}
    return [
        {**area, "cache_disponivel": area["id"] in area_ids_with_cache}
        for area in areas_res.data
    ]
