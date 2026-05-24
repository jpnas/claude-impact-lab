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
        raise HTTPException(status_code=404, detail="Área não encontrada")
    return result
