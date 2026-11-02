import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer

def detect(df, columns, contamination=0.05):
    if not columns or any(c not in df.select_dtypes(include="number").columns for c in columns): raise ValueError("Elegí columnas numéricas válidas.")
    if len(df) < 20: raise ValueError("Se necesitan al menos 20 filas.")
    x = df[columns].replace([np.inf, -np.inf], np.nan)
    if x.isna().all().any(): raise ValueError("Una columna seleccionada no tiene valores válidos.")
    if not any(x[c].nunique(dropna=True) > 1 for c in columns): raise ValueError("Los datos no tienen variación suficiente.")
    x = SimpleImputer(strategy="median").fit_transform(x)
    model = IsolationForest(contamination=contamination, random_state=42)
    labels = model.fit_predict(x)
    result = df.copy()
    result["puntuacion_anomalia"] = model.decision_function(x)
    result["anomalia"] = labels == -1
    return result
