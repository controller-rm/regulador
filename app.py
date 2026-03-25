import streamlit as st

st.set_page_config(
    page_title="Teste Deploy",
    page_icon="✅",
    layout="wide"
)

st.title("Teste de Deploy")
st.success("Aplicação carregada com sucesso!")
st.write("Se você está vendo esta tela, o deploy do Streamlit está funcionando.")
