import streamlit as st
import pandas as pd

def exibir_relatorios(df):
    pessoa = st.selectbox("Filtrar por pessoa", [""] + list(df["pessoa"].dropna().unique()))
    categoria = st.selectbox("Filtrar por categoria", [""] + list(df["categoria"].dropna().unique()))
    status = st.selectbox("Status", [""] + list(df["status"].dropna().unique()))
    filtro = df.copy()
    if pessoa: filtro = filtro[filtro["pessoa"] == pessoa]
    if categoria: filtro = filtro[filtro["categoria"] == categoria]
    if status: filtro = filtro[filtro["status"] == status]
    st.write(filtro)
    st.write("Total:", filtro["valor"].sum())
    if not filtro.empty:
        filtro["mes"] = pd.to_datetime(filtro["data"], dayfirst=True).dt.strftime("%Y-%m")
        st.bar_chart(filtro.groupby("mes")["valor"].sum())
