"""
Capa de acceso a datos. Los CSV hacen las veces de "base de datos":

  - data/clientes.csv          -> variables originales de cada cliente
                                   (simula la tabla de clientes del banco).
  - data/ofertas_enviadas.csv  -> registro de cada oferta de retencion
                                   simulada, para hacer seguimiento.

Nada de esto depende de FastAPI: son funciones planas sobre pandas.
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CLIENTES_CSV = DATA_DIR / "clientes.csv"
OFERTAS_CSV = DATA_DIR / "ofertas_enviadas.csv"

OFERTAS_COLUMNS = [
    "id", "clientnum", "oferta_id", "oferta_nombre", "canal",
    "correo_destino", "fecha_envio", "estado_seguimiento", "fecha_actualizacion",
]

ESTADOS_SEGUIMIENTO = ["enviada", "contactado", "aceptada", "rechazada", "sin_respuesta"]

# Catalogo de ofertas de retencion (fijo, no requiere CSV aparte).
CATALOGO_OFERTAS: list[dict[str, Any]] = [
    {
        "id": "tasa_preferencial",
        "nombre": "Tasa de interes preferencial",
        "descripcion": "3 meses con una reduccion de la tasa de interes de la tarjeta.",
        "beneficio": "-30% sobre la tasa actual durante 3 meses",
        "icono": "percent",
    },
    {
        "id": "cuota_manejo_exenta",
        "nombre": "Exencion de cuota de manejo",
        "descripcion": "6 meses sin cobro de la cuota de manejo de la tarjeta.",
        "beneficio": "0 cuota de manejo durante 6 meses",
        "icono": "shield",
    },
    {
        "id": "cashback_doble",
        "nombre": "Cashback x2 en compras",
        "descripcion": "Duplica los puntos/cashback en todas las compras durante 60 dias.",
        "beneficio": "2x cashback durante 60 dias",
        "icono": "gift",
    },
]

_lock = threading.Lock()


def obtener_catalogo_ofertas() -> list[dict[str, Any]]:
    return CATALOGO_OFERTAS


def obtener_oferta_por_id(oferta_id: str) -> dict[str, Any] | None:
    for oferta in CATALOGO_OFERTAS:
        if oferta["id"] == oferta_id:
            return oferta
    return None


def leer_clientes() -> pd.DataFrame:
    if not CLIENTES_CSV.exists():
        raise FileNotFoundError(
            f"No existe {CLIENTES_CSV}. Ejecuta scripts/train_model.py primero."
        )
    return pd.read_csv(CLIENTES_CSV)


def _asegurar_ofertas_csv() -> None:
    if not OFERTAS_CSV.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=OFERTAS_COLUMNS).to_csv(OFERTAS_CSV, index=False)


def leer_ofertas_enviadas() -> pd.DataFrame:
    _asegurar_ofertas_csv()
    df = pd.read_csv(OFERTAS_CSV)
    for col in OFERTAS_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[OFERTAS_COLUMNS]


def guardar_oferta_enviada(
    clientnum: int, oferta_id: str, oferta_nombre: str, correo_destino: str
) -> dict[str, Any]:
    """Agrega un registro de oferta enviada (simulada) y devuelve el registro creado."""
    with _lock:
        df = leer_ofertas_enviadas()
        nuevo_id = int(df["id"].max()) + 1 if len(df) else 1
        registro = {
            "id": nuevo_id,
            "clientnum": int(clientnum),
            "oferta_id": oferta_id,
            "oferta_nombre": oferta_nombre,
            "canal": "email",
            "correo_destino": correo_destino,
            "fecha_envio": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "estado_seguimiento": "enviada",
            "fecha_actualizacion": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
        df.to_csv(OFERTAS_CSV, index=False)
        return registro


def actualizar_estado_oferta(oferta_envio_id: int, nuevo_estado: str) -> dict[str, Any] | None:
    """Actualiza el estado de seguimiento de una oferta enviada. Devuelve el
    registro actualizado, o None si no existe."""
    if nuevo_estado not in ESTADOS_SEGUIMIENTO:
        raise ValueError(f"Estado invalido: {nuevo_estado}. Validos: {ESTADOS_SEGUIMIENTO}")

    with _lock:
        df = leer_ofertas_enviadas()
        mascara = df["id"] == oferta_envio_id
        if not mascara.any():
            return None
        df.loc[mascara, "estado_seguimiento"] = nuevo_estado
        df.loc[mascara, "fecha_actualizacion"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        df.to_csv(OFERTAS_CSV, index=False)
        return df.loc[mascara].iloc[0].to_dict()


def clientes_con_oferta_enviada() -> set[int]:
    """CLIENTNUMs que ya tienen al menos una oferta registrada (para marcar
    'ya contactado' en el dashboard)."""
    df = leer_ofertas_enviadas()
    if df.empty:
        return set()
    return set(df["clientnum"].astype(int).tolist())
