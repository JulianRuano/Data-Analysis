from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .. import services

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.get("")
def get_clientes(
    riesgo_min: float = Query(0, ge=0, le=100, description="Probabilidad minima de cancelacion (%)"),
    riesgo_max: float = Query(100, ge=0, le=100, description="Probabilidad maxima de cancelacion (%)"),
    nivel_riesgo: Optional[str] = Query(None, description="bajo | moderado | alto | critico"),
    genero: Optional[str] = Query(None, alias="genero"),
    education_level: Optional[str] = None,
    marital_status: Optional[str] = None,
    income_category: Optional[str] = None,
    card_category: Optional[str] = None,
    attrition_flag: Optional[str] = None,
    oferta_enviada: Optional[bool] = Query(None, description="Filtrar por si ya se le envio una oferta"),
    buscar_clientnum: Optional[str] = Query(None, description="Busqueda parcial por CLIENTNUM"),
    ordenar_por: str = Query("probabilidad_cancelacion"),
    orden: str = Query("desc", pattern="^(asc|desc)$"),
    pagina: int = Query(1, ge=1),
    tamano_pagina: int = Query(20, ge=1, le=200),
):
    """Lista clientes con su riesgo de cancelacion predicho, con filtros,
    orden y paginacion. Pensado para alimentar la tabla del dashboard."""
    return services.listar_clientes(
        riesgo_min=riesgo_min,
        riesgo_max=riesgo_max,
        nivel_riesgo=nivel_riesgo,
        genero=genero,
        education_level=education_level,
        marital_status=marital_status,
        income_category=income_category,
        card_category=card_category,
        attrition_flag=attrition_flag,
        oferta_enviada=oferta_enviada,
        buscar_clientnum=buscar_clientnum,
        ordenar_por=ordenar_por,
        orden=orden,
        pagina=pagina,
        tamano_pagina=tamano_pagina,
    )


@router.get("/filtros")
def get_opciones_filtros():
    """Valores unicos disponibles (para poblar los <select> del frontend)."""
    return services.opciones_filtros()


@router.get("/{clientnum}")
def get_cliente(clientnum: int):
    cliente = services.obtener_cliente(clientnum)
    if cliente is None:
        raise HTTPException(status_code=404, detail=f"No existe el cliente {clientnum}")
    return cliente
