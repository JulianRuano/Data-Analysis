from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routers import clientes, dashboard, ofertas

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Prediccion de Cancelacion de Tarjeta de Credito",
    description=(
        "Solucion analitica predictiva para identificar clientes con alta "
        "probabilidad de cancelar su tarjeta de credito y gestionar campanas "
        "de retencion proactivas."
    ),
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")

app.include_router(clientes.router)
app.include_router(dashboard.router)
app.include_router(ofertas.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/api/health")
def health():
    return {"status": "ok"}
