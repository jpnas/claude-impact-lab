from __future__ import annotations
import uuid
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
    area = db.execute("SELECT id FROM areas WHERE slug = ?", (slug,)).fetchone()
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    if reuniao_id:
        row = db.execute(
            "SELECT * FROM relatorios WHERE area_id = ? AND reuniao_id = ? ORDER BY criado_em DESC LIMIT 1",
            (area["id"], reuniao_id),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT * FROM relatorios WHERE area_id = ? ORDER BY criado_em DESC LIMIT 1",
            (area["id"],),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    return dict(row)


@router.put("/{slug}/relatorio")
def salvar_relatorio(slug: str, body: SalvarBody):
    db = get_db()
    area = db.execute("SELECT id FROM areas WHERE slug = ?", (slug,)).fetchone()
    if not area:
        raise HTTPException(status_code=404, detail="Área não encontrada")

    rel_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO relatorios (id, area_id, reuniao_id, conteudo, status) VALUES (?, ?, ?, ?, ?)",
        (rel_id, area["id"], body.reuniao_id, body.conteudo, body.status),
    )
    db.commit()
    row = db.execute("SELECT * FROM relatorios WHERE id = ?", (rel_id,)).fetchone()
    return dict(row)
