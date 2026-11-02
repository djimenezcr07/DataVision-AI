from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from .anomaly import detect
from .io import load

def run_local(dataset="ventas"):
    if dataset == "iris":
        from sklearn.datasets import load_iris
        bunch = load_iris(as_frame=True)
        df = bunch.frame
        df["especie"] = df.pop("target").map(dict(enumerate(bunch.target_names)))
        source = "Iris de Fisher, copia distribuida con scikit-learn; UCI Machine Learning Repository: https://archive.ics.uci.edu/dataset/53/iris — licencia CC BY 4.0."
    else:
        path = Path(__file__).resolve().parents[1] / "examples" / "ventas.csv"
        df = load(path.read_bytes(), path.name)
        source = "Ejemplo local sintético de ventas, creado para este proyecto; sin datos personales ni fuente pública."
    numeric = list(df.select_dtypes(include="number").columns)
    try:
        result = detect(df, numeric)
        anomaly = f"{int(result['anomalia'].sum())} registros señalados por Isolation Forest (semilla 42, contaminación 5 %)."
    except ValueError as exc: anomaly = f"No se ejecutó: {exc}"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stats = df[numeric].describe().round(2).to_string() if numeric else "Sin columnas numéricas."
    report = f"""# Informe DataVision AI

## Fuente y fecha
{source} Consulta: {stamp}.

## Calidad
- Filas: {len(df)}; columnas: {len(df.columns)}.
- Celdas faltantes: {int(df.isna().sum().sum())}; filas duplicadas: {int(df.duplicated().sum())}.

## Estadísticas descriptivas
```
{stats}
```

## Anomalías
{anomaly}

## Metodología y límites
Se validó el archivo, se calcularon métricas descriptivas y se intentó detectar observaciones inusuales con mediana para valores faltantes. Los resultados describen únicamente el conjunto seleccionado. Una anomalía estadística no implica error ni fraude. Las visualizaciones se muestran en la aplicación; este informe conserva los valores calculados. No se aplicaron transformaciones al archivo de origen.
"""
    return df, report
