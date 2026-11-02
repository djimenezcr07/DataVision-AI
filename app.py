import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datavision.io import load, sheets, quality
from datavision.forge import transform
from datavision.sql import query
from datavision.anomaly import detect
from datavision.report import run_local

st.set_page_config(page_title="DataVision AI", page_icon="◈", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 2rem; max-width: 1400px;}
h1,h2,h3 {letter-spacing:-0.035em;} [data-testid="stSidebar"] {background:#171d38;}
[data-testid="stSidebar"] * {color:#f5f5ff !important;} [data-testid="stMetric"] {background:white; border:1px solid #e6e9f4; border-radius:16px; padding:18px; box-shadow:0 6px 25px #2028450a;}
.hero {padding:24px 28px; border-radius:20px; background:linear-gradient(110deg,#20284e,#6b5bd6); color:white; margin-bottom:22px;}
.hero small {color:#c8c5ff; letter-spacing:.16em; font-weight:700;} .hero h1 {color:white; margin:8px 0;} .hero p {color:#e2e3fa; margin:0;}
</style>""", unsafe_allow_html=True)
for k,v in {"original":None,"data":None,"history":[],"source":""}.items():
    if k not in st.session_state: st.session_state[k]=v

def set_data(df, source):
    st.session_state.original=df.copy(deep=True); st.session_state.data=df.copy(deep=True); st.session_state.history=[]; st.session_state.source=source

def csv(df): return df.to_csv(index=False).encode("utf-8-sig")
def download(df, name): st.download_button("↓ Descargar CSV",csv(df),name,"text/csv")

with st.sidebar:
    st.markdown("## ◈ DataVision AI")
    st.caption("TU ESPACIO DE ANÁLISIS")
    page=st.radio("Navegación",["Inicio y carga","DataForge","Consultas SQL","Dashboard","Anomalías","Agente e informes"], label_visibility="collapsed")
    st.divider()
    if st.session_state.data is not None:
        st.caption("DATASET ACTIVO")
        st.write(st.session_state.source)
        st.caption(f"{len(st.session_state.data):,} filas · {len(st.session_state.data.columns)} columnas")
    else: st.info("Cargá un archivo para comenzar.")
    st.caption("Análisis local · Sin API externa")

st.markdown(f'<div class="hero"><small>DATAVISION AI / {page.upper()}</small><h1>{page}</h1><p>De datos sin procesar a decisiones mejor informadas.</p></div>',unsafe_allow_html=True)
if page == "Inicio y carga":
    st.subheader("Empezá con tus datos")
    st.write("Importá un CSV o Excel, o explorá el ejemplo sintético incluido. Los archivos se procesan localmente en esta aplicación.")
    a,b=st.columns([1,1])
    with a:
        if st.button("Usar ejemplo de ventas", type="primary"):
            path=Path(__file__).parent/"examples"/"ventas.csv"; set_data(load(path.read_bytes(),path.name),"Ventas sintéticas")
    with b: st.caption("CSV / XLSX · Hasta 10 MB · Sin modificar el original")
    uploaded=st.file_uploader("Elegí un archivo",type=["csv","xlsx"])
    if uploaded:
        data=uploaded.getvalue(); sep=","; enc="utf-8"; sheet=0
        try:
            if uploaded.name.lower().endswith(".xlsx"): sheet=st.selectbox("Hoja",sheets(data))
            else:
                c1,c2=st.columns(2)
                with c1: sep=st.selectbox("Separador",[",",";","\t","|"])
                with c2: enc=st.selectbox("Codificación",["utf-8","utf-8-sig","latin-1"])
            if st.button("Cargar archivo"):
                frame=load(data,uploaded.name,sep,enc,sheet); set_data(frame,uploaded.name); st.success("Archivo cargado correctamente.")
        except Exception as e: st.error(str(e))
    if st.session_state.data is not None:
        df=st.session_state.data; st.divider(); st.subheader("Vista general")
        a,b,c,d=st.columns(4); a.metric("Filas",f"{len(df):,}"); b.metric("Columnas",len(df.columns)); c.metric("Valores faltantes",int(df.isna().sum().sum())); d.metric("Duplicados",int(df.duplicated().sum()))
        st.dataframe(df.head(100),use_container_width=True); st.dataframe(quality(df),use_container_width=True,hide_index=True)

elif page == "Agente e informes":
    st.subheader("Análisis guiado y reproducible")
    st.write("Este flujo controlado valida un conjunto, calcula calidad y estadísticas, crea dos gráficos y, si es posible, detecta anomalías. No es un agente autónomo general.")
    dataset = st.selectbox("Conjunto", ["Ventas sintéticas locales", "Iris público (copia incluida en scikit-learn)"])
    st.info("Iris: Fisher / UCI Machine Learning Repository, CC BY 4.0: https://archive.ics.uci.edu/dataset/53/iris. La copia de scikit-learn funciona sin conexión. Las ventas son sintéticas.")
    if st.button("Generar informe local", type="primary"):
        df,report=run_local("iris" if dataset.startswith("Iris") else "ventas"); st.session_state.report=report; st.session_state.report_data=df
    if "report" in st.session_state:
        df=st.session_state.report_data
        x,y=st.columns(2)
        numeric=list(df.select_dtypes(include="number").columns); category="especie" if "especie" in df else "categoria"
        with x: st.plotly_chart(px.histogram(df,x=numeric[0],title="Distribución numérica",color_discrete_sequence=["#7964f6"]),use_container_width=True)
        with y: st.plotly_chart(px.bar(df.groupby(category,as_index=False)[numeric[0]].mean(),x=category,y=numeric[0],title="Promedio por categoría",color_discrete_sequence=["#4cc6b7"]),use_container_width=True)
        st.download_button("↓ Descargar informe Markdown",st.session_state.report,"informe.md","text/markdown")
        with st.expander("Ver informe"): st.markdown(st.session_state.report)

elif st.session_state.data is None:
    st.info("Primero cargá un archivo o elegí el ejemplo en Inicio y carga.")
else:
    df=st.session_state.data; cols=list(df.columns); nums=list(df.select_dtypes(include="number").columns)
    if page == "DataForge":
        st.subheader("Prepará tus datos")
        st.caption("Cada cambio se aplica a una copia; si falla, el dataset actual se conserva intacto.")
        choices=["Eliminar duplicados","Eliminar filas con faltantes","Rellenar faltantes","Cambiar tipo","Renombrar columna","Eliminar columnas","Filtrar filas"]
        choice=st.selectbox("Operación",choices); action=""; kw={}
        if choice==choices[0]: action="duplicados"
        elif choice==choices[1]: action="eliminar_faltantes"; kw={"columns":st.multiselect("Columnas obligatorias",cols)}
        elif choice==choices[2]:
            action="rellenar"; kw={"column":st.selectbox("Columna",cols),"method":st.selectbox("Método",["valor","media","mediana","moda"]),"value":st.text_input("Valor para relleno manual")}
        elif choice==choices[3]: action="tipo"; kw={"column":st.selectbox("Columna",cols),"dtype":st.selectbox("Nuevo tipo",["numérico","texto","fecha"])}
        elif choice==choices[4]: action="renombrar"; kw={"column":st.selectbox("Columna",cols),"name":st.text_input("Nuevo nombre")}
        elif choice==choices[5]: action="eliminar_columnas"; kw={"columns":st.multiselect("Columnas a eliminar",cols)}
        else: action="filtrar"; kw={"column":st.selectbox("Columna",cols),"operator":st.selectbox("Operador",["=","≠",">","<","contiene"]),"value":st.text_input("Valor")}
        a,b=st.columns(2)
        with a:
            if st.button("Aplicar operación",type="primary"):
                try:
                    updated=transform(df,action,**kw); st.session_state.data=updated; st.session_state.history.append(f"{choice}: {kw}"); st.rerun()
                except ValueError as e: st.error(str(e))
        with b:
            if st.button("Restablecer original"):
                st.session_state.data=st.session_state.original.copy(deep=True); st.session_state.history=[]; st.rerun()
        st.caption("Historial de esta sesión")
        if st.session_state.history:
            for item in st.session_state.history: st.write("•",item)
        else: st.write("Aún no hay operaciones aplicadas.")
        st.dataframe(df.head(100),use_container_width=True); download(df,"datos_procesados.csv")
    elif page == "Consultas SQL":
        st.subheader("Consultá la tabla datos")
        st.caption("SELECT con expresiones y agregaciones básicas. Máximo 1.000 filas; no se permiten archivos externos, subconsultas ni funciones arbitrarias.")
        sql=st.text_area("Consulta SQL", "SELECT categoria, SUM(cantidad) AS total FROM datos GROUP BY categoria ORDER BY total DESC")
        if st.button("Ejecutar consulta", type="primary"):
            try: st.session_state.sql_result=query(df,sql); st.session_state.sql_source=id(df)
            except ValueError as e: st.error(str(e)); st.session_state.pop("sql_result",None)
        if "sql_result" in st.session_state and st.session_state.get("sql_source")==id(df): st.dataframe(st.session_state.sql_result,use_container_width=True); download(st.session_state.sql_result,"consulta.csv")
    elif page == "Dashboard":
        st.subheader("Explorá patrones")
        a,b,c=st.columns(3); a.metric("Registros",len(df)); b.metric("Faltantes",int(df.isna().sum().sum())); c.metric("Columnas numéricas",len(nums))
        filtered=df
        filter_col=st.selectbox("Filtrar por columna",["Sin filtro"]+cols)
        if filter_col != "Sin filtro":
            vals=sorted(df[filter_col].dropna().astype(str).unique().tolist())
            chosen=st.multiselect("Valores",vals)
            if chosen: filtered=df[df[filter_col].astype(str).isin(chosen)]
        if nums:
            metric=st.selectbox("Estadística numérica",nums); st.caption(f"Media: {filtered[metric].mean():,.2f} · Mediana: {filtered[metric].median():,.2f}")
        kind=st.selectbox("Gráfico",["Barras","Líneas","Dispersión","Histograma"])
        if not nums: st.info("Se necesita al menos una columna numérica para estos gráficos.")
        else:
            x=st.selectbox("Eje X",cols); y=st.selectbox("Eje Y",nums) if kind != "Histograma" else None
            if kind=="Barras": fig=px.bar(filtered,x=x,y=y)
            elif kind=="Líneas": fig=px.line(filtered,x=x,y=y)
            elif kind=="Dispersión": fig=px.scatter(filtered,x=x,y=y)
            else: fig=px.histogram(filtered,x=x)
            fig.update_layout(template="plotly_white",margin=dict(l=10,r=10,t=30,b=10),colorway=["#7964f6","#4cc6b7"]); st.plotly_chart(fig,use_container_width=True)
            if kind=="Líneas":
                dates=pd.to_datetime(filtered[x],errors="coerce") if not pd.api.types.is_numeric_dtype(filtered[x]) else pd.Series(dtype="datetime64[ns]")
                valid=filtered.assign(_fecha=dates).dropna(subset=["_fecha",y]).sort_values("_fecha")
                if len(valid)>=2: st.caption(f"Descripción: entre {valid['_fecha'].iloc[0].date()} y {valid['_fecha'].iloc[-1].date()}, {y} pasó de {valid[y].iloc[0]:,.2f} a {valid[y].iloc[-1]:,.2f}. Esto no explica la causa.")
    elif page == "Anomalías":
        st.subheader("Observaciones inusuales")
        st.write("Isolation Forest identifica registros estadísticamente distintos. Una anomalía no implica necesariamente error ni fraude.")
        selected=st.multiselect("Columnas numéricas",nums,default=nums[:2]); contamination=st.slider("Proporción esperada",0.01,0.30,0.05,0.01)
        if st.button("Detectar anomalías",type="primary"):
            try: st.session_state.anomaly_result=detect(df,selected,contamination); st.session_state.anomaly_source=id(df)
            except ValueError as e: st.error(str(e)); st.session_state.pop("anomaly_result",None)
        if "anomaly_result" in st.session_state and st.session_state.get("anomaly_source")==id(df):
            result=st.session_state.anomaly_result; flagged=result[result.anomalia].sort_values("puntuacion_anomalia"); st.metric("Registros señalados",len(flagged)); st.dataframe(flagged,use_container_width=True); download(result,"anomalias.csv")
