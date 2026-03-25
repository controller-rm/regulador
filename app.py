import streamlit as st
import reposicao_estoque
import consumo

st.set_page_config(
    page_title="Painel de Reposição",
    page_icon="📦",
    layout="wide"
)

menu = st.sidebar.selectbox(
    "Selecione a análise",
    ["Reposição de Estoque"]
)

if menu == "Reposição de Estoque":
    reposicao_estoque.main()
else:
    reposicao_estoque.main()
