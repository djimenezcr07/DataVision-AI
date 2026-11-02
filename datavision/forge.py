import pandas as pd

def transform(df, action, **kw):
    """Trabaja sobre una copia y devuelve el resultado solo si toda la operación funciona."""
    out = df.copy(deep=True)
    try:
        if action == "duplicados": out = out.drop_duplicates()
        elif action == "eliminar_faltantes":
            if not kw["columns"]: raise ValueError("Elegí al menos una columna.")
            out = out.dropna(subset=kw["columns"])
        elif action == "rellenar":
            col, method = kw["column"], kw["method"]
            s = out[col]
            if method in ("media", "mediana"):
                if not pd.api.types.is_numeric_dtype(s): raise ValueError("La media y mediana requieren una columna numérica.")
                value = s.mean() if method == "media" else s.median()
            elif method == "moda":
                if s.mode().empty: raise ValueError("No hay valores para calcular la moda.")
                value = s.mode().iloc[0]
            else:
                value = kw["value"]
                if pd.api.types.is_numeric_dtype(s): value = pd.to_numeric(value, errors="raise")
            if pd.isna(value): raise ValueError("No se pudo calcular un valor de relleno.")
            out[col] = s.fillna(value)
        elif action == "tipo":
            col, typ = kw["column"], kw["dtype"]
            if typ == "numérico": out[col] = pd.to_numeric(out[col], errors="raise")
            elif typ == "fecha": out[col] = pd.to_datetime(out[col], errors="raise")
            elif typ == "texto": out[col] = out[col].astype("string")
        elif action == "renombrar":
            name = kw["name"].strip()
            if not name or (name in out.columns and name != kw["column"]): raise ValueError("El nombre debe ser único y no estar vacío.")
            out = out.rename(columns={kw["column"]: name})
        elif action == "eliminar_columnas":
            if not kw["columns"] or len(kw["columns"]) >= len(out.columns): raise ValueError("Seleccioná columnas y conservá al menos una.")
            out = out.drop(columns=kw["columns"])
        elif action == "filtrar":
            s = out[kw["column"]]; value = kw["value"]
            if pd.api.types.is_numeric_dtype(s): value = pd.to_numeric(value, errors="raise")
            elif pd.api.types.is_datetime64_any_dtype(s): value = pd.to_datetime(value, errors="raise")
            op = kw["operator"]
            mask = {"=": lambda: s == value, "≠": lambda: s != value, ">": lambda: s > value, "<": lambda: s < value, "contiene": lambda: s.astype("string").str.contains(str(value), case=False, regex=False, na=False)}[op]()
            out = out.loc[mask.fillna(False)]
        else: raise ValueError("Operación desconocida.")
        return out.reset_index(drop=True)
    except Exception as exc:
        raise ValueError(f"No se aplicó la operación: {exc}") from exc
