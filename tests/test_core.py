from pathlib import Path
from io import BytesIO
import pandas as pd
import pytest
from datavision.io import load, sheets
from datavision.forge import transform
from datavision.sql import query
from datavision.anomaly import detect
from datavision.report import run_local

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def sales(): return load((ROOT/"examples/ventas.csv").read_bytes(),"ventas.csv")

def test_load_and_excel(sales):
    assert len(sales)==81
    data=(ROOT/"examples/ejemplo.xlsx").read_bytes()
    assert len(sheets(data))==2
    assert len(load(data,"ejemplo.xlsx",sheet="Ventas"))==81
    assert len(load(data,"ejemplo.xlsx",sheet="Categorias"))==3

@pytest.mark.parametrize("data,name",[(b"","v.csv"),(b"bad","x.xlsx"),(b"a,b\n1,2","x.txt"),(b"a,b\n","x.csv")])
def test_invalid_files(data,name):
    with pytest.raises(ValueError): load(data,name)

def test_atomic_transform(sales):
    before=sales.copy(deep=True)
    with pytest.raises(ValueError): transform(sales,"renombrar",column="fecha",name="precio")
    pd.testing.assert_frame_equal(before,sales)
    assert len(transform(sales,"duplicados"))==80
    assert not transform(sales,"rellenar",column="precio",method="mediana")["precio"].isna().any()
    with pytest.raises(ValueError): transform(sales,"tipo",column="categoria",dtype="numérico")
    pd.testing.assert_frame_equal(before,sales)

def test_sql_read(sales):
    result=query(sales,"SELECT categoria, SUM(cantidad) AS total FROM datos GROUP BY categoria ORDER BY total DESC")
    assert len(result)==3
    assert len(query(sales,"SELECT * FROM datos",limit=5))==5

@pytest.mark.parametrize("sql",["DELETE FROM datos", "SELECT * FROM read_csv('secret.csv')", "SELECT * FROM datos; SELECT * FROM datos", "INSTALL httpfs", "SELECT * FROM datos, read_csv('/etc/passwd')", "SELECT * FROM (SELECT * FROM datos)"])
def test_sql_denied(sales,sql):
    with pytest.raises(ValueError): query(sales,sql)

def test_anomaly(sales):
    result=detect(sales,["cantidad","precio"])
    assert result.anomalia.sum()>0
    with pytest.raises(ValueError): detect(sales.head(5),["precio"])
    with pytest.raises(ValueError): detect(pd.DataFrame({"x":[1]*30}),["x"])

def test_report():
    df,report=run_local()
    assert len(df)==81 and "sintético" in report and "Metodología" in report
