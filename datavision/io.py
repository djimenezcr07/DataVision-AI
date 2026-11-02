from io import BytesIO
import pandas as pd

MAX_BYTES = 10 * 1024 * 1024

def sheets(data: bytes) -> list[str]:
    _check(data)
    try:
        return pd.ExcelFile(BytesIO(data), engine="openpyxl").sheet_names
    except Exception as exc:
        raise ValueError("No se pudo leer el Excel; verificá que no esté dañado.") from exc

def _check(data: bytes):
    if not data:
        raise ValueError("El archivo está vacío.")
    if len(data) > MAX_BYTES:
        raise ValueError("El archivo supera el límite de 10 MB.")

def load(data: bytes, name: str, separator=",", encoding="utf-8", sheet=0):
    _check(data)
    try:
        if name.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(data), sep=separator, encoding=encoding)
        elif name.lower().endswith(".xlsx"):
            df = pd.read_excel(BytesIO(data), sheet_name=sheet, engine="openpyxl")
        else:
            raise ValueError("Formato no admitido: usá CSV o XLSX.")
        if df.empty or not len(df.columns):
            raise ValueError("El archivo no contiene filas de datos.")
        df.columns = [str(c) for c in df.columns]
        if any(not c.strip() for c in df.columns) or df.columns.duplicated().any():
            raise ValueError("Los nombres de columnas deben ser únicos y no vacíos.")
        return df
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"No se pudo procesar el archivo: {exc}") from exc

def quality(df):
    return pd.DataFrame({"columna": df.columns, "tipo": df.dtypes.astype(str).values, "faltantes": df.isna().sum().values})
