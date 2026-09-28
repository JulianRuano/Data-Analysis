"""
Logica de negocio: combina datos de clientes.csv + predicciones del modelo +
ofertas_enviadas.csv, y aplica filtros/orden/paginacion.

Todas las funciones son planas (reciben y devuelven dict/DataFrame) para
poder probarlas sin FastAPI.
"""
from __future__ import annotations

import math
from typing import Any, Optional

import pandas as pd

from . import database
from .ml import clasificar_riesgo, predecir_riesgo

COLOR_POR_NIVEL = {
    "critico": "#ef4444",
    "alto": "#f97316",
    "moderado": "#eab308",
    "bajo": "#22c55e",
}


def _dataframe_clientes_con_riesgo() -> pd.DataFrame:
    df = database.leer_clientes()
    riesgo_pct = predecir_riesgo(df)
    df = df.copy()
    df["probabilidad_cancelacion"] = riesgo_pct.round(2)

    niveles = [clasificar_riesgo(p) for p in riesgo_pct]
    df["nivel_riesgo"] = [n["nivel"] for n in niveles]
    df["nivel_riesgo_slug"] = [n["slug"] for n in niveles]
    df["color_riesgo"] = [COLOR_POR_NIVEL[n["slug"]] for n in niveles]

    ya_contactados = database.clientes_con_oferta_enviada()
    df["oferta_enviada"] = df["CLIENTNUM"].astype(int).isin(ya_contactados)

    return df


def _cliente_a_dict(fila: pd.Series) -> dict[str, Any]:
    d = fila.to_dict()
    # Normaliza tipos numpy -> tipos nativos para que sean serializables en JSON.
    for k, v in d.items():
        if isinstance(v, (pd.Timestamp,)):
            d[k] = v.isoformat()
        elif hasattr(v, "item"):
            d[k] = v.item()
    d["CLIENTNUM"] = int(d["CLIENTNUM"])
    d["nombre_display"] = f"Cliente #{d['CLIENTNUM']}"
    d["correo_demo"] = f"cliente{d['CLIENTNUM']}@demo-correo.com"
    return d


def listar_clientes(
    riesgo_min: float = 0.0,
    riesgo_max: float = 100.0,
    nivel_riesgo: Optional[str] = None,
    genero: Optional[str] = None,
    education_level: Optional[str] = None,
    marital_status: Optional[str] = None,
    income_category: Optional[str] = None,
    card_category: Optional[str] = None,
    attrition_flag: Optional[str] = None,
    oferta_enviada: Optional[bool] = None,
    buscar_clientnum: Optional[str] = None,
    ordenar_por: str = "probabilidad_cancelacion",
    orden: str = "desc",
    pagina: int = 1,
    tamano_pagina: int = 20,
) -> dict[str, Any]:
    df = _dataframe_clientes_con_riesgo()

    df = df[(df["probabilidad_cancelacion"] >= riesgo_min) & (df["probabilidad_cancelacion"] <= riesgo_max)]

    if nivel_riesgo:
        df = df[df["nivel_riesgo_slug"] == nivel_riesgo.lower()]
    if genero:
        df = df[df["Gender"].str.upper() == genero.upper()]
    if education_level:
        df = df[df["Education_Level"] == education_level]
    if marital_status:
        df = df[df["Marital_Status"] == marital_status]
    if income_category:
        df = df[df["Income_Category"] == income_category]
    if card_category:
        df = df[df["Card_Category"] == card_category]
    if attrition_flag:
        df = df[df["Attrition_Flag"] == attrition_flag]
    if oferta_enviada is not None:
        df = df[df["oferta_enviada"] == oferta_enviada]
    if buscar_clientnum:
        df = df[df["CLIENTNUM"].astype(str).str.contains(buscar_clientnum.strip())]

    columnas_validas = set(df.columns)
    if ordenar_por not in columnas_validas:
        ordenar_por = "probabilidad_cancelacion"
    df = df.sort_values(by=ordenar_por, ascending=(orden.lower() == "asc"))

    total = len(df)
    tamano_pagina = max(1, min(tamano_pagina, 200))
    pagina = max(1, pagina)
    total_paginas = max(1, math.ceil(total / tamano_pagina))
    pagina = min(pagina, total_paginas)

    inicio = (pagina - 1) * tamano_pagina
    fin = inicio + tamano_pagina
    pagina_df = df.iloc[inicio:fin]

    clientes = [_cliente_a_dict(fila) for _, fila in pagina_df.iterrows()]

    return {
        "clientes": clientes,
        "total": total,
        "pagina": pagina,
        "tamano_pagina": tamano_pagina,
        "total_paginas": total_paginas,
    }


def obtener_cliente(clientnum: int) -> dict[str, Any] | None:
    df = _dataframe_clientes_con_riesgo()
    fila = df[df["CLIENTNUM"].astype(int) == int(clientnum)]
    if fila.empty:
        return None
    return _cliente_a_dict(fila.iloc[0])


def opciones_filtros() -> dict[str, list[str]]:
    """Valores unicos disponibles para poblar los <select> de filtros en el frontend."""
    df = database.leer_clientes()
    return {
        "education_level": sorted(df["Education_Level"].unique().tolist()),
        "marital_status": sorted(df["Marital_Status"].unique().tolist()),
        "income_category": sorted(df["Income_Category"].unique().tolist()),
        "card_category": sorted(df["Card_Category"].unique().tolist()),
        "gender": sorted(df["Gender"].unique().tolist()),
        "attrition_flag": sorted(df["Attrition_Flag"].unique().tolist()),
    }


def resumen_dashboard() -> dict[str, Any]:
    df = _dataframe_clientes_con_riesgo()
    total_clientes = len(df)
    en_riesgo = df[df["probabilidad_cancelacion"] >= 50]
    ofertas_enviadas_df = database.leer_ofertas_enviadas()

    distribucion = {
        slug: int((df["nivel_riesgo_slug"] == slug).sum())
        for slug in ["bajo", "moderado", "alto", "critico"]
    }

    return {
        "total_clientes": total_clientes,
        "total_en_riesgo": int(len(en_riesgo)),
        "porcentaje_en_riesgo": round(100 * len(en_riesgo) / total_clientes, 1) if total_clientes else 0,
        "probabilidad_promedio": round(float(df["probabilidad_cancelacion"].mean()), 1) if total_clientes else 0,
        "distribucion_riesgo": distribucion,
        "total_ofertas_enviadas": int(len(ofertas_enviadas_df)),
        "ofertas_por_estado": (
            ofertas_enviadas_df["estado_seguimiento"].value_counts().to_dict()
            if not ofertas_enviadas_df.empty else {}
        ),
        "clientes_pendientes_contacto": int(len(en_riesgo[~en_riesgo["oferta_enviada"]])),
    }


class ClienteNoEncontradoError(Exception):
    pass


class OfertaNoEncontradaError(Exception):
    pass


def enviar_oferta(clientnum: int, oferta_id: str) -> dict[str, Any]:
    cliente = obtener_cliente(clientnum)
    if cliente is None:
        raise ClienteNoEncontradoError(f"No existe el cliente {clientnum}")

    oferta = database.obtener_oferta_por_id(oferta_id)
    if oferta is None:
        raise OfertaNoEncontradaError(f"No existe la oferta {oferta_id}")

    correo_destino = cliente["correo_demo"]
    registro = database.guardar_oferta_enviada(
        clientnum=clientnum,
        oferta_id=oferta["id"],
        oferta_nombre=oferta["nombre"],
        correo_destino=correo_destino,
    )

    correo_simulado = {
        "para": correo_destino,
        "asunto": f"Tenemos una oferta especial para ti, {cliente['nombre_display']}",
        "cuerpo": (
            f"Hola {cliente['nombre_display']},\n\n"
            f"Queremos que sigas disfrutando tu tarjeta {cliente['Card_Category']}. "
            f"Por eso te ofrecemos: {oferta['nombre']} - {oferta['beneficio']}.\n\n"
            f"{oferta['descripcion']}\n\n"
            "Responde este correo o contacta a tu asesor para activarla.\n\n"
            "Equipo de Retencion de Clientes"
        ),
    }

    return {"registro": registro, "correo_simulado": correo_simulado}


def listar_ofertas_enviadas(
    estado_seguimiento: Optional[str] = None,
    clientnum: Optional[int] = None,
) -> list[dict[str, Any]]:
    df = database.leer_ofertas_enviadas()
    if estado_seguimiento:
        df = df[df["estado_seguimiento"] == estado_seguimiento]
    if clientnum is not None:
        df = df[df["clientnum"].astype(int) == int(clientnum)]
    df = df.sort_values(by="fecha_envio", ascending=False)
    return df.to_dict(orient="records")


def actualizar_seguimiento(oferta_envio_id: int, nuevo_estado: str) -> dict[str, Any]:
    registro = database.actualizar_estado_oferta(oferta_envio_id, nuevo_estado)
    if registro is None:
        raise OfertaNoEncontradaError(f"No existe el envio de oferta con id {oferta_envio_id}")
    return registro
