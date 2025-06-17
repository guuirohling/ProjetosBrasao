import streamlit as st
import pandas as pd

def mostrar_resumo(df):
    st.header("Resumo - Tabela Dinâmica")
    if df.empty:
        st.info("Sem dados.")
        return

    pessoa_col = st.selectbox("Agrupar por:", ["quem_paga", "pessoa_deve"])
    if pessoa_col:
        tabela = pd.pivot_table(df, index=[pessoa_col], columns=["banco"], values="valor", aggfunc="sum", fill_value=0, margins=True, margins_name="Total")
        st.dataframe(tabela.style.format("R$ {:.2f}"))
