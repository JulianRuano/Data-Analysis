# Retencion de Clientes - Prediccion de cancelacion de tarjeta de credito

Aplicacion monolitica (FastAPI + Jinja2 + un modelo de Regresion Logistica)
que expone una API y un dashboard  para identificar clientes con alta
probabilidad de cancelar su tarjeta de credito y gestionar ofertas de
retencion.

## Estructura

```
churn_app/
├── Dockerfile
├── requirements.txt
├── model/
│   └── modelo_churn.joblib        # modelo + scaler + metadatos (generado)
├── data/
│   ├── clientes.csv               # "base de datos" simulada (30 clientes)
│   └── ofertas_enviadas.csv       # seguimiento de ofertas enviadas
├── scripts/
│   ├── data_generator.py          # generador de clientes sinteticos
│   └── train_model.py             # entrena el modelo y crea los CSV demo
└── app/
    ├── main.py                    # app FastAPI (rutas HTML + monta routers)
    ├── ml.py                      # carga del modelo + transformacion + prediccion
    ├── database.py                # lectura/escritura de los CSV ("BD")
    ├── services.py                # logica de negocio (filtros, ofertas, resumen)
    ├── schemas.py                 # modelos Pydantic de entrada
    ├── routers/
    │   ├── clientes.py            # GET /api/clientes, /api/clientes/{id}, /api/clientes/filtros
    │   ├── dashboard.py           # GET /api/dashboard/resumen
    │   └── ofertas.py             # /api/ofertas/*
    ├── templates/                 # Jinja2 (base.html, index.html)
    └── static/                    # CSS/JS del dashboard
```

## Construir y ejecutar con Docker

```bash
cd churn_app
docker build -t retencion-clientes .
docker run -p 8000:8000 retencion-clientes
```

Abrir http://localhost:8000

Para conservar los cambios del CSV de ofertas entre reinicios del contenedor,
monta la carpeta `data/` como volumen:

```bash
docker run -p 8000:8000 -v "$(pwd)/data:/app/data" retencion-clientes
```

## Ejecutar sin Docker (para desarrollo)

```bash
pip install -r requirements.txt
python scripts/train_model.py      # solo la primera vez / para re-entrenar
uvicorn app.main:app --reload
```

## Regenerar el modelo y los datos demo

`scripts/train_model.py` reproduce exactamente el pipeline de preparacion
ya validado (seleccion de variables, one-hot con `pandas.get_dummies` y
`StandardScaler` sobre las numericas) sobre un dataset sintetico con el
esquema original de BankChurners, entrena la Regresion Logistica y:

- guarda `model/modelo_churn.joblib` (modelo + scaler + columnas + categorias)
- regenera `data/clientes.csv` con 30 clientes de ejemplo con una distribucion
  variada de riesgo (bajo/moderado/alto/critico)
- crea `data/ofertas_enviadas.csv` vacio si no existe

Para usar tu propio `BankChurners.csv` real en lugar de datos sinteticos,
reemplaza la llamada a `generar_clientes(...)` en `entrenar()` y
`elegir_30_clientes_demo(...)` por `pd.read_csv("tu_archivo.csv")`, siempre
que tenga las columnas originales (`CLIENTNUM`, `Attrition_Flag`,
`Customer_Age`, `Gender`, ... `Avg_Utilization_Ratio`).

## Principales endpoints

| Metodo | Ruta | Descripcion |
|---|---|---|
| GET | `/api/clientes` | Lista clientes con riesgo predicho. Filtros: `riesgo_min`, `riesgo_max`, `nivel_riesgo`, `genero`, `education_level`, `marital_status`, `income_category`, `card_category`, `attrition_flag`, `oferta_enviada`, `buscar_clientnum`, `ordenar_por`, `orden`, `pagina`, `tamano_pagina` |
| GET | `/api/clientes/filtros` | Valores unicos disponibles para los selects |
| GET | `/api/clientes/{clientnum}` | Detalle de un cliente |
| GET | `/api/dashboard/resumen` | KPIs agregados |
| GET | `/api/ofertas/catalogo` | Las 3 ofertas de retencion disponibles |
| POST | `/api/ofertas/enviar` | `{clientnum, oferta_id}` -> simula el envio de un correo y registra el seguimiento |
| GET | `/api/ofertas/enviadas` | Historial de ofertas enviadas (filtros: `estado_seguimiento`, `clientnum`) |
| PATCH | `/api/ofertas/enviadas/{id}` | `{estado_seguimiento}` -> actualiza el seguimiento |

## Niveles de riesgo

| Rango | Nivel | Color |
|---|---|---|
| 0% - 29.9% | Bajo | verde |
| 30% - 49.9% | Moderado | amarillo |
| 50% - 69.9% | Alto | naranja |
| 70% - 100% | Critico | rojo |

El dashboard destaca por defecto a los clientes con **riesgo >= 50%** como
alertas de retencion.
