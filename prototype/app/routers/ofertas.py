from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .. import database, services
from ..schemas import ActualizarSeguimientoRequest, EnviarOfertaRequest

router = APIRouter(prefix="/api/ofertas", tags=["ofertas"])


@router.get("/catalogo")
def get_catalogo():
    """Las 3 ofertas de retencion disponibles para enviar a un cliente."""
    return database.obtener_catalogo_ofertas()


@router.post("/enviar")
def post_enviar_oferta(payload: EnviarOfertaRequest):
    """Simula el envio de un correo con la oferta seleccionada y deja
    registro para seguimiento."""
    try:
        resultado = services.enviar_oferta(payload.clientnum, payload.oferta_id)
    except services.ClienteNoEncontradoError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except services.OfertaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return resultado


@router.get("/enviadas")
def get_ofertas_enviadas(
    estado_seguimiento: Optional[str] = Query(None),
    clientnum: Optional[int] = Query(None),
):
    """Historial de ofertas enviadas, para la pestana de seguimiento."""
    return services.listar_ofertas_enviadas(estado_seguimiento=estado_seguimiento, clientnum=clientnum)


@router.patch("/enviadas/{oferta_envio_id}")
def patch_seguimiento(oferta_envio_id: int, payload: ActualizarSeguimientoRequest):
    """Actualiza el estado de seguimiento de una oferta ya enviada."""
    try:
        return services.actualizar_seguimiento(oferta_envio_id, payload.estado_seguimiento)
    except services.OfertaNoEncontradaError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
