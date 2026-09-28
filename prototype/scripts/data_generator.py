"""
Generador de datos sinteticos con el esquema ORIGINAL de BankChurners.

Se usa para:
  1) Generar un dataset grande de entrenamiento (con senal real para que
     la regresion logistica aprenda patrones de churn, no ruido puro).
  2) Poblar la "base de datos" (data/clientes.csv) con 30 clientes de
     ejemplo para que el dashboard tenga algo que mostrar.

No requiere el CSV real de Kaggle: recrea la misma estructura de columnas
y distribuciones aproximadas del dataset BankChurners.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

GENDERS = ["M", "F"]
EDUCATION_LEVELS = [
    "High School", "Graduate", "Uneducated", "Unknown",
    "College", "Post-Graduate", "Doctorate",
]
MARITAL_STATUSES = ["Married", "Single", "Unknown", "Divorced"]
INCOME_CATEGORIES = [
    "Less than $40K", "$40K - $60K", "$60K - $80K",
    "$80K - $120K", "$120K +", "Unknown",
]
CARD_CATEGORIES = ["Blue", "Silver", "Gold", "Platinum"]

# Orden EXACTO de columnas originales solicitado (con Total_Relationship_Count
# completando el "..." del dataset BankChurners estandar).
RAW_COLUMNS = [
    "CLIENTNUM", "Attrition_Flag", "Customer_Age", "Gender", "Dependent_count",
    "Education_Level", "Marital_Status", "Income_Category", "Card_Category",
    "Months_on_book", "Total_Relationship_Count", "Months_Inactive_12_mon",
    "Contacts_Count_12_mon", "Credit_Limit", "Total_Revolving_Bal",
    "Avg_Open_To_Buy", "Total_Amt_Chng_Q4_Q1", "Total_Trans_Amt",
    "Total_Trans_Ct", "Total_Ct_Chng_Q4_Q1", "Avg_Utilization_Ratio",
]


def generar_clientes(n: int, seed: int = 42, clientnum_start: int = 768800000) -> pd.DataFrame:
    """Genera n clientes sinteticos con el esquema original de BankChurners.

    Las variables numericas estan correlacionadas con un "riesgo latente"
    interno para que el modelo entrenado sobre estos datos tenga patrones
    reales que aprender (menos transacciones, mas inactividad -> mas riesgo).
    """
    rng = np.random.default_rng(seed)

    riesgo_latente = rng.beta(2, 5, size=n)  # sesgado hacia clientes leales

    customer_age = np.clip(rng.normal(46, 8, n), 26, 73).round().astype(int)
    dependent_count = rng.integers(0, 6, n)
    months_on_book = np.clip(rng.normal(36, 8, n), 13, 56).round().astype(int)
    total_relationship_count = rng.integers(1, 7, n)

    months_inactive = np.clip(rng.normal(1 + 4 * riesgo_latente, 1), 0, 6).round().astype(int)
    contacts_count = np.clip(rng.normal(1 + 3.5 * riesgo_latente, 1), 0, 6).round().astype(int)

    credit_limit = np.clip(rng.lognormal(mean=8.7, sigma=0.9, size=n), 1438, 34516).round(2)
    avg_utilization_ratio = np.clip(rng.beta(1.5, 2 + 3 * riesgo_latente, n), 0, 0.999).round(3)
    total_revolving_bal = (credit_limit * avg_utilization_ratio).round(2)
    avg_open_to_buy = np.clip(credit_limit - total_revolving_bal, 0, None).round(2)

    total_amt_chng_q4_q1 = np.clip(rng.normal(0.76 - 0.3 * riesgo_latente, 0.2, n), 0, 3.4).round(3)
    total_ct_chng_q4_q1 = np.clip(rng.normal(0.71 - 0.3 * riesgo_latente, 0.2, n), 0, 3.7).round(3)

    total_trans_ct = np.clip(rng.normal(65 - 45 * riesgo_latente, 15, n), 10, 139).round().astype(int)
    total_trans_amt = np.clip(rng.normal(4400 - 2500 * riesgo_latente, 1500, n), 510, 18484).round(2)

    gender = rng.choice(GENDERS, n, p=[0.47, 0.53])
    education_level = rng.choice(EDUCATION_LEVELS, n, p=[0.31, 0.30, 0.06, 0.11, 0.13, 0.05, 0.04])
    marital_status = rng.choice(MARITAL_STATUSES, n, p=[0.46, 0.39, 0.07, 0.08])
    income_category = rng.choice(INCOME_CATEGORIES, n, p=[0.35, 0.17, 0.15, 0.13, 0.10, 0.10])
    card_category = rng.choice(CARD_CATEGORIES, n, p=[0.93, 0.05, 0.01, 0.01])

    prob_attrition = np.clip(riesgo_latente * 0.8 + rng.normal(0, 0.08, n), 0, 1)
    attrition_flag = np.where(
        rng.random(n) < prob_attrition, "Attrited Customer", "Existing Customer"
    )

    clientnum = clientnum_start + np.arange(n) * 7 + rng.integers(0, 7, n)

    df = pd.DataFrame({
        "CLIENTNUM": clientnum,
        "Attrition_Flag": attrition_flag,
        "Customer_Age": customer_age,
        "Gender": gender,
        "Dependent_count": dependent_count,
        "Education_Level": education_level,
        "Marital_Status": marital_status,
        "Income_Category": income_category,
        "Card_Category": card_category,
        "Months_on_book": months_on_book,
        "Total_Relationship_Count": total_relationship_count,
        "Months_Inactive_12_mon": months_inactive,
        "Contacts_Count_12_mon": contacts_count,
        "Credit_Limit": credit_limit,
        "Total_Revolving_Bal": total_revolving_bal,
        "Avg_Open_To_Buy": avg_open_to_buy,
        "Total_Amt_Chng_Q4_Q1": total_amt_chng_q4_q1,
        "Total_Trans_Amt": total_trans_amt,
        "Total_Trans_Ct": total_trans_ct,
        "Total_Ct_Chng_Q4_Q1": total_ct_chng_q4_q1,
        "Avg_Utilization_Ratio": avg_utilization_ratio,
    })

    return df[RAW_COLUMNS]
