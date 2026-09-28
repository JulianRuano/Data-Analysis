"""
Entrena la Regresion Logistica de prediccion de cancelacion (churn) y deja
listo todo lo que la API necesita:

  - model/modelo_churn.joblib        -> modelo + scaler + metadatos de columnas
  - data/clientes.csv                -> "base de datos" con 30 clientes demo
  - data/ofertas_enviadas.csv        -> archivo vacio de seguimiento de ofertas

Reproduce EXACTAMENTE la transformacion que ya se valido para el CSV
preparado (selected_features, one-hot con pandas.get_dummies y
StandardScaler sobre las numericas), para que el modelo entrenado aqui
sea compatible con ese mismo criterio de preparacion.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_generator import generar_clientes  # noqa: E402
from app.ml import transformar_con_artifact, predecir_con_artifact  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "model"
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = MODEL_DIR / "modelo_churn.joblib"
CLIENTES_CSV = DATA_DIR / "clientes.csv"
OFERTAS_CSV = DATA_DIR / "ofertas_enviadas.csv"

RANDOM_STATE = 42

# ---- Mismas variables seleccionadas para el modelo (pipeline del usuario) ----
selected_features = [
    "Customer_Age",
    "Gender",
    "Education_Level",
    "Marital_Status",
    "Income_Category",
    "Card_Category",
    "Credit_Limit",
    "Total_Trans_Amt",
    "Total_Trans_Ct",
    "Avg_Utilization_Ratio",
]
target = "Attrition_Flag"

categorical_features = [
    "Gender",
    "Education_Level",
    "Marital_Status",
    "Income_Category",
    "Card_Category",
]
numeric_features = [
    "Customer_Age",
    "Credit_Limit",
    "Total_Trans_Amt",
    "Total_Trans_Ct",
    "Avg_Utilization_Ratio",
]

OFERTAS_COLUMNS = [
    "id", "clientnum", "oferta_id", "oferta_nombre", "canal",
    "correo_destino", "fecha_envio", "estado_seguimiento", "fecha_actualizacion",
]


def preparar_dataframe(df_raw: pd.DataFrame):
    """Replica el pipeline de preparacion del usuario y devuelve
    (X, y, scaler, categories, feature_columns)."""
    required_columns = selected_features + [target]
    missing_columns = sorted(set(required_columns) - set(df_raw.columns))
    if missing_columns:
        raise KeyError(f"Faltan columnas requeridas: {missing_columns}")

    df_sin_transformar = df_raw[required_columns].copy()

    df_modelo = df_sin_transformar.copy()
    df_modelo[target] = df_modelo[target].eq("Attrited Customer").astype(int)

    encoded_categoricals = pd.get_dummies(
        df_modelo[categorical_features],
        columns=categorical_features,
        dtype=int,
    )
    scaler = StandardScaler()
    scaled_numerics = pd.DataFrame(
        scaler.fit_transform(df_modelo[numeric_features]),
        columns=numeric_features,
        index=df_modelo.index,
    )
    df_logistica = pd.concat([scaled_numerics, encoded_categoricals], axis=1)

    feature_columns = list(df_logistica.columns)
    categories = {
        feat: sorted(df_modelo[feat].astype(str).unique().tolist())
        for feat in categorical_features
    }

    return df_logistica, df_modelo[target], scaler, categories, feature_columns


def entrenar():
    print("Generando dataset sintetico de entrenamiento...")
    df_train_raw = generar_clientes(n=4000, seed=123, clientnum_start=700000000)

    X, y, scaler, categories, feature_columns = preparar_dataframe(df_train_raw)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    modelo = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    y_proba = modelo.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1": round(float(f1_score(y_test, y_pred)), 4),
        "auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    print("Metricas del modelo (holdout de prueba):", metrics)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": modelo,
        "scaler": scaler,
        "selected_features": selected_features,
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "categories": categories,
        "feature_columns": feature_columns,
        "target": target,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
    joblib.dump(artifact, MODEL_PATH)
    print(f"Modelo guardado en: {MODEL_PATH}")

    return artifact


def elegir_30_clientes_demo(artifact: dict) -> pd.DataFrame:
    """Genera candidatos y elige 30 con una distribucion de riesgo variada
    (para que el dashboard tenga clientes en todos los niveles de alerta)."""
    candidatos = generar_clientes(n=600, seed=7, clientnum_start=768800000)
    X_cand = transformar_con_artifact(candidatos, artifact)
    proba = predecir_con_artifact(artifact, X_cand) * 100

    candidatos = candidatos.copy()
    candidatos["_riesgo"] = proba

    bajo = candidatos[candidatos["_riesgo"] < 30].sample(n=11, random_state=1)
    moderado = candidatos[(candidatos["_riesgo"] >= 30) & (candidatos["_riesgo"] < 50)].sample(n=7, random_state=2)
    alto = candidatos[(candidatos["_riesgo"] >= 50) & (candidatos["_riesgo"] < 70)].sample(n=7, random_state=3)
    critico = candidatos[candidatos["_riesgo"] >= 70].sample(n=5, random_state=4)

    seleccion = pd.concat([bajo, moderado, alto, critico]).drop(columns="_riesgo")
    seleccion = seleccion.sample(frac=1, random_state=99).reset_index(drop=True)  # mezclar orden
    return seleccion


def generar_datos_demo(artifact: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    clientes_demo = elegir_30_clientes_demo(artifact)
    clientes_demo.to_csv(CLIENTES_CSV, index=False)
    print(f"data/clientes.csv generado con {len(clientes_demo)} clientes en: {CLIENTES_CSV}")

    if not OFERTAS_CSV.exists():
        pd.DataFrame(columns=OFERTAS_COLUMNS).to_csv(OFERTAS_CSV, index=False)
        print(f"data/ofertas_enviadas.csv (vacio) creado en: {OFERTAS_CSV}")


if __name__ == "__main__":
    artifact = entrenar()
    generar_datos_demo(artifact)
