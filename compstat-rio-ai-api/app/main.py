from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.action_plan import build_action_plan
from app.services.chat import build_chat_response
from app.services.data_loader import load_area_data
from app.services.risk import enrich_segments
from app.services.summary import build_executive_summary


class ChatRequest(BaseModel):
    message: str


app = FastAPI(
    title="CompStat Rio AI API",
    description="FastAPI backend for CompStat Rio AI operational intelligence.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://10.115.130.94:3000",
        "http://10.115.130.94:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/area")
def get_area() -> dict[str, Any]:
    area_data = load_area_data()

    return {
        **area_data,
        "segments": enrich_segments(area_data["segments"]),
    }


@app.get("/summary")
def get_summary() -> dict[str, Any]:
    return build_executive_summary()


@app.get("/action-plan")
def get_action_plan() -> dict[str, list[dict[str, Any]]]:
    return {"actions": build_action_plan()}


@app.post("/chat")
def post_chat(request: ChatRequest) -> dict[str, str]:
    message = request.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    return {"answer": build_chat_response(message)}
