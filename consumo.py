# import streamlit as st
# from services.consumo_service import (
#     preparar_dataframe_consumo,
#     resumo_consumo_material,
#     consumo_diario_material,
#     preparar_csv_brasileiro,
#     formatar_numero_br,
# )


# def render_card_resumo(titulo, valor, subtitulo="", cor_fundo="#f6e3e6"):
#     st.markdown(
#         f"""
#         <div style="
#             background:{cor_fundo};
#             border-radius:18px;
#             padding:18px 20px;
#             box-shadow:0 2px 10px rgba(0,0,0,0.08);
#             min-height:120px;
#             margin-bottom:10px;
#         ">
#             <div style="
#                 font-size:15px;
#                 font-weight:700;
#                 color:#4b5563;
#                 margin-bottom:10px;
#             ">
#                 {titulo}
#             </div>
#             <div style="
#                 font-size:22px;
#                 font-weight:800;
#                 color:#111827;
#                 margin-bottom:8px;
#             ">
#                 {valor}
#             </div>
#             <div style="
#                 font-size:13px;
#                 color:#374151;
#                 line-height:1.6;
#                 white-space:pre-line;
#             ">
#                 {subtitulo}
#             </div>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )


# def main():
#     st.title("Consumo de Materiais")
#     st.caption("Análise do consumo líquido por material com base na tabela REQUISICOES.")

#     st.markdown(
#         """
#         <style>
#             .block-container {
#                 padding-top: 1rem;
#                 padding-bottom: 1rem;
#             }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

#     try:
#         st.sidebar.header("Filtros")

#         periodo_dias = st.sidebar.selectbox(
#             "Período de consumo (dias)",
#             options=[30, 60, 90, 120, 180, 365],
#             index=0
#         )

#         df = preparar_dataframe_consumo(dias=periodo_dias)

#         if df.empty:
#             st.warning("Nenhum registro encontrado para o período informado.")
#             return

#         resumo = resumo_consumo_material(df)
#         diario = consumo_diario_material(df)

#         st.success(f"{len(df)} movimentações carregadas com sucesso.")

#         total_movimentos = len(df)
#         total_materiais = resumo["material"].nunique() if "material" in resumo.columns else 0
#         consumo_total_geral = resumo["consumo_total"].sum() if "consumo_total" in resumo.columns else 0
#         custo_total_geral = resumo["custo_total_consumo"].sum() if "custo_total_consumo" in resumo.columns else 0

#         dias_unicos = df["data"].nunique() if "data" in df.columns else 0
#         dias_unicos = max(dias_unicos, 1)
#         media_diaria_geral = consumo_total_geral / dias_unicos

#         st.markdown("### Indicadores Gerais")
#         with st.expander("Indicadores Gerais", expanded=False):
#             col1, col2, col3, col4 = st.columns(4)

#             with col1:
#                 render_card_resumo(
#                     "Movimentações",
#                     formatar_numero_br(total_movimentos, 0),
#                     f"Período analisado: {periodo_dias} dias",
#                     "#eef2ff"
#                 )

#             with col2:
#                 render_card_resumo(
#                     "Materiais",
#                     formatar_numero_br(total_materiais, 0),
#                     "Quantidade de materiais com consumo no período",
#                     "#f0fdf4"
#                 )

#             with col3:
#                 render_card_resumo(
#                     "Consumo Total",
#                     formatar_numero_br(consumo_total_geral, 2),
#                     f"Média diária geral: {formatar_numero_br(media_diaria_geral, 2)}",
#                     "#fee2e2"
#                 )

#             with col4:
#                 render_card_resumo(
#                     "Custo Total",
#                     formatar_numero_br(custo_total_geral, 2),
#                     "Saldo líquido considerando requisição e devolução",
#                     "#fef3c7"
#                 )

#         opcoes_material = sorted(resumo["material"].dropna().astype(str).unique().tolist()) if "material" in resumo.columns else []
#         opcoes_unidade = sorted(resumo["unidade"].dropna().astype(str).unique().tolist()) if "unidade" in resumo.columns else []

#         filtro_material = st.sidebar.multiselect(
#             "Material",
#             options=opcoes_material
#         )

#         filtro_unidade = st.sidebar.multiselect(
#             "Unidade",
#             options=opcoes_unidade,
#             default=opcoes_unidade
#         )

#         filtro_somente_positivo = st.sidebar.checkbox(
#             "Exibir somente consumo líquido positivo",
#             value=False
#         )

#         resumo_filtrado = resumo.copy()

#         if filtro_material and "material" in resumo_filtrado.columns:
#             resumo_filtrado = resumo_filtrado[resumo_filtrado["material"].isin(filtro_material)]

#         if filtro_unidade and "unidade" in resumo_filtrado.columns:
#             resumo_filtrado = resumo_filtrado[resumo_filtrado["unidade"].isin(filtro_unidade)]

#         if filtro_somente_positivo and "consumo_total" in resumo_filtrado.columns:
#             resumo_filtrado = resumo_filtrado[resumo_filtrado["consumo_total"] > 0]

#         st.markdown("### Resultado")

#         todas_colunas = list(resumo_filtrado.columns)

#         colunas_padrao = [
#             "material",
#             "desc_material",
#             "unidade",
#             "consumo_total",
#             "consumo_diario",
#             "custo_total_consumo",
#             "total_movimentos",
#             "dias_com_movimento",
#         ]

#         colunas_padrao = [col for col in colunas_padrao if col in todas_colunas]

#         colunas_visiveis = st.sidebar.multiselect(
#             "Colunas visíveis na tabela",
#             options=todas_colunas,
#             default=colunas_padrao
#         )

#         if not colunas_visiveis:
#             st.warning("Selecione ao menos uma coluna para exibir a tabela.")
#             return

#         df_exibicao = resumo_filtrado[colunas_visiveis].copy()

#         colunas_formatar = [
#             "consumo_total",
#             "consumo_diario",
#             "custo_total_consumo",
#         ]

#         for col in colunas_formatar:
#             if col in df_exibicao.columns:
#                 df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_numero_br(x, 2))

#         if "total_movimentos" in df_exibicao.columns:
#             try:
#                 df_exibicao["total_movimentos"] = df_exibicao["total_movimentos"].fillna(0).astype(int)
#             except Exception:
#                 pass

#         if "dias_com_movimento" in df_exibicao.columns:
#             try:
#                 df_exibicao["dias_com_movimento"] = df_exibicao["dias_com_movimento"].fillna(0).astype(int)
#             except Exception:
#                 pass

#         st.dataframe(
#             df_exibicao,
#             use_container_width=True,
#             hide_index=True
#         )

#         csv = preparar_csv_brasileiro(resumo_filtrado)

#         st.download_button(
#             label="Baixar CSV",
#             data=csv,
#             file_name="consumo_materiais.csv",
#             mime="text/csv"
#         )

#     except Exception as e:
#         st.error(f"Erro ao carregar os dados: {e}")