"""Modelos Pydantic para validar entradas/salidas de la API."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class EnviarOfertaRequest(BaseModel):
    clientnum: int = Field(..., description="CLIENTNUM del cliente destino")
    oferta_id: str = Field(..., description="Id de la oferta del catalogo (ver /api/ofertas/catalogo)")


class ActualizarSeguimientoRequest(BaseModel):
    estado_seguimiento: str = Field(
        ..., description="Nuevo estado: enviada | contactado | aceptada | rechazada | sin_respuesta"
    )
