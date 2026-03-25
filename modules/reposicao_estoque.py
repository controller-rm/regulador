import streamlit as st

def main():
    st.set_page_config(
        page_title="Teste Deploy",
        page_icon="✅",
        layout="wide"
    )

    st.title("Painel de Reposição")
    st.success("✅ Aplicação carregada com sucesso!")

    st.write("Se você está vendo essa mensagem, o deploy está funcionando corretamente.")
