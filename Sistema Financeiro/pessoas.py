import streamlit as st
import pandas as pd
from persistence import carregar_pessoas, salvar_pessoas

def gerenciar_pessoas():
    st.header("Cadastro de Pessoas")
    pessoas = carregar_pessoas()
    novo_nome = st.text_input("Nova pessoa:")
    if st.button("Adicionar pessoa"):
        if novo_nome and novo_nome not in pessoas["nome"].values:
            # CORREÇÃO: usar concat ao invés de append
            pessoas = pd.concat([pessoas, pd.DataFrame([{"nome": novo_nome}])], ignore_index=True)
            salvar_pessoas(pessoas)
            st.success("Pessoa adicionada.")
    if not pessoas.empty:
        nomes = pessoas["nome"].tolist()
        excluir = st.selectbox("Excluir pessoa", [""] + nomes)
        if excluir and st.button("Excluir selecionada"):
            pessoas = pessoas[pessoas["nome"] != excluir]
            salvar_pessoas(pessoas)
            st.success("Pessoa excluída.")
    st.write(pessoas)
