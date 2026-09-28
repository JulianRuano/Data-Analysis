"""
Carga del modelo entrenado y transformacion de clientes "crudos" (variables
originales) al mismo formato numerico que espera la Regresion Logistica.

Esta capa NO depende de FastAPI: solo de pandas / sklearn / joblib, para
que se pueda probar de forma aislada.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "modelo_churn.joblib"

# Umbrales de riesgo (en %) usados en todo el dashboard.
NIVELES_RIESGO = [
    (70.0, "Critico", "critico"),
    (50.0, "Alto", "alto"),
    (30.0, "Moderado", "moderado"),
    (0.0, "Bajo", "bajo"),
]

_artifact_cache: dict[str, Any] | None = None


def cargar_artifact(forzar_recarga: bool = False) -> dict[str, Any]:
    """Carga (con cache en memoria) el artifact guardado por train_model.py."""
    global _artifact_cache
    if _artifact_cache is None or forzar_recarga:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"No se encontro el modelo entrenado en {MODEL_PATH}. "
                "Ejecuta scripts/train_model.py primero."
            )
        _artifact_cache = joblib.load(MODEL_PATH)
    return _artifact_cache


def transformar_con_artifact(df_raw: pd.DataFrame, artifact: dict[str, Any]) -> pd.DataFrame:
    """Aplica sobre df_raw (variables originales) la MISMA transformacion
    usada al preparar BankChurners_preparado.csv: selecciona columnas,
    escala numericas con el scaler ya ajustado y aplica one-hot alineado
    a las categorias vistas en entrenamiento."""
    selected_features = artifact["selected_features"]
    categorical_features = artifact["categorical_features"]
    numeric_features = artifact["numeric_features"]
    categories = artifact["categories"]
    feature_columns = artifact["feature_columns"]
    scaler = artifact["scaler"]

    faltantes = sorted(set(selected_features) - set(df_raw.columns))
    if faltantes:
        raise KeyError(f"Faltan columnas requeridas para predecir: {faltantes}")

    df = df_raw[selected_features].copy()

    scaled = pd.DataFrame(
        scaler.transform(df[numeric_features]),
        columns=numeric_features,
        index=df.index,
    )

    frames = [scaled]
    for feat in categorical_features:
        cats = categories[feat]
        col = pd.Categorical(df[feat].astype(str), categories=cats)
        dummies = pd.get_dummies(col, prefix=feat, dtype=int)
        frames.append(dummies)

    X = pd.concat(frames, axis=1)
    X = X.reindex(columns=feature_columns, fill_value=0)
    return X


def predecir_con_artifact(artifact: dict[str, Any], X: pd.DataFrame) -> np.ndarray:
    """Devuelve un array de probabilidades (0-1) de cancelacion."""
    modelo = artifact["model"]
    return modelo.predict_proba(X)[:, 1]


def predecir_riesgo(df_raw: pd.DataFrame) -> np.ndarray:
    """Atajo: carga el artifact global, transforma y predice.
    Devuelve probabilidades en PORCENTAJE (0-100)."""
    artifact = cargar_artifact()
    X = transformar_con_artifact(df_raw, artifact)
    proba = predecir_con_artifact(artifact, X)
    return proba * 100


def clasificar_riesgo(pct: float) -> dict[str, str]:
    """Clasifica un porcentaje de riesgo en un nivel (Bajo/Moderado/Alto/Critico)."""
    for umbral, nombre, slug in NIVELES_RIESGO:
        if pct >= umbral:
            return {"nivel": nombre, "slug": slug}
    return {"nivel": "Bajo", "slug": "bajo"}
