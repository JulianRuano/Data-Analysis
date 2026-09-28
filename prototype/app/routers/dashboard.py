from __future__ import annotations

from fastapi import APIRouter

from .. import services

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/resumen")
def get_resumen():
    """KPIs agregados para las tarjetas superiores del dashboard."""
    return services.resumen_dashboard()
