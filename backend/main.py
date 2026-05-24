from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import areas, relatorios

app = FastAPI(title="CompStat Rio API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(areas.router)
app.include_router(relatorios.router)


@app.get("/health")
def health():
    return {"status": "ok"}
