import streamlit as st
from modules import reposicao_estoque

st.set_page_config(
    page_title="Painel de Reposição",
    page_icon="📦",
    layout="wide"
)

reposicao_estoque.main()
