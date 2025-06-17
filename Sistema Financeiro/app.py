import streamlit as st
import pandas as pd
from extrator import extrair_texto_pdf, identificar_banco_e_titular, extrair_lancamentos
from persistence import carregar_lancamentos, salvar_lancamentos, carregar_pessoas
from pessoas import gerenciar_pessoas
from resumo import mostrar_resumo
import datetime

st.set_page_config(layout="wide")
st.title("Gestão de Faturas de Cartão (PDF Multi-banco e Multi-pessoa)")

menu = st.sidebar.radio("Menu", ["Importar Faturas", "Classificar/Editar", "Pessoas", "Resumo"])

if menu == "Importar Faturas":
    st.header("Importar Múltiplos PDFs de Fatura")
    arquivos = st.file_uploader("Selecione os PDFs", type=["pdf"], accept_multiple_files=True)
    senha = st.text_input("Senha do PDF (se necessário):", type="password")
    if arquivos:
        todos = []
        for file in arquivos:
            texto = extrair_texto_pdf(file, senha if senha else None)
            banco, titular = identificar_banco_e_titular(texto)
            lanc = extrair_lancamentos(texto, banco, titular)
            todos.append(lanc)
        if todos:
            novos = pd.concat(todos, ignore_index=True)
            st.write(novos)
            if st.button("Adicionar ao histórico"):
                df = carregar_lancamentos()
                df = pd.concat([df, novos], ignore_index=True)
                salvar_lancamentos(df)
                st.success("Lançamentos adicionados.")

elif menu == "Classificar/Editar":
    st.header("Classificação e Edição dos Lançamentos")
    df = carregar_lancamentos()
    if df.empty:
        st.info("Nenhum lançamento importado ainda.")
    else:
        pessoas = carregar_pessoas()["nome"].tolist()
        # Se não existem pessoas cadastradas, não libera edição
        if not pessoas:
            st.warning("Cadastre pelo menos uma pessoa antes de editar os lançamentos.")
        else:
            campos_editaveis = ["categoria", "quem_paga", "pessoa_deve"]
            for col in campos_editaveis:
                if col not in df.columns:
                    df[col] = ""
            # Permite edição em tabela (Ctrl+C / Ctrl+V)
            edit_df = st.data_editor(
                df,
                column_order=list(df.columns),
                disabled=["data", "descricao", "valor", "banco", "titular"],
                num_rows="dynamic",
                use_container_width=True,
                key="editor"
            )
            st.markdown(
                """
                <span style="color: #666;">
                <b>Dica:</b> Você pode selecionar blocos de células, copiar (Ctrl+C) de uma planilha ou da própria tabela acima e colar (Ctrl+V) nos campos editáveis.<br>
                Edite vários lançamentos de uma vez e clique em <b>Salvar alterações</b> para persistir tudo!
                </span>
                """, unsafe_allow_html=True
            )
            if st.button("Salvar alterações"):
                for col in campos_editaveis:
                    df[col] = edit_df[col]
                salvar_lancamentos(df)
                st.success("Alterações salvas.")

elif menu == "Pessoas":
    gerenciar_pessoas()

elif menu == "Resumo":
    df = carregar_lancamentos()
    mostrar_resumo(df)
    st.header("Status de Pagamento (por total)")
    if not df.empty:
        df["mes"] = pd.to_datetime(df["data"], errors="coerce").dt.to_period("M").astype(str)
        pessoas = carregar_pessoas()["nome"].tolist()
        grupo = st.multiselect("Selecione pessoas para o resumo:", pessoas)
        if grupo:
            filtrado = df[df["quem_paga"].isin(grupo)]
            tabela = pd.pivot_table(
                filtrado,
                index=["quem_paga", "mes"],
                columns=["banco"],
                values="valor",
                aggfunc="sum",
                fill_value=0,
                margins=True,
                margins_name="Total"
            )
            st.dataframe(tabela.style.format("R$ {:.2f}"))
            pago = st.checkbox("Marcar como pago?")
            if pago:
                st.info(
                    "No MVP, o status de pagamento é visual. Em versões futuras, pode-se criar um campo e permitir editar por pessoa/mês/banco.")
