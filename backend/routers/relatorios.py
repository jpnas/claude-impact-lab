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
    area = db.table("areas").select("id").eq("slug", slug).execute()
    if not area.data:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    query = (
        db.table("relatorios")
        .select("*")
        .eq("area_id", area.data[0]["id"])
    )
    if reuniao_id:
        query = query.eq("reuniao_id", reuniao_id)
    res = query.order("criado_em", desc=True).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return res.data[0]


@router.put("/{slug}/relatorio")
def salvar_relatorio(slug: str, body: SalvarBody):
    db = get_db()
    area = db.table("areas").select("id").eq("slug", slug).execute()
    if not area.data:
        raise HTTPException(status_code=404, detail="Área não encontrada")
    res = db.table("relatorios").insert(
        {
            "area_id": area.data[0]["id"],
            "reuniao_id": body.reuniao_id,
            "conteudo": body.conteudo,
            "status": body.status,
        }
    ).execute()
    return res.data[0]
