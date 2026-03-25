import streamlit as st
from services.produto_service import preparar_dataframe_produtos


def colorir_semaforo(valor):
    if valor == "VERMELHO":
        return "background-color: #f8d7da; color: #842029; font-weight: bold;"
    elif valor == "AMARELO":
        return "background-color: #fff3cd; color: #664d03; font-weight: bold;"
    elif valor == "VERDE":
        return "background-color: #d1e7dd; color: #0f5132; font-weight: bold;"
    return ""


def formatar_numero_br(valor, casas=2):
    try:
        return f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return valor


def preparar_csv_brasileiro(df):
    df_export = df.copy()

    colunas_numericas = [
        "quantidade",
        "estoque_minimo",
        "dias_reposicao_fornecedor",
        "pedidos_em_aberto",
        "reserva_planejamento",
        "solicit_compras",
        "compras_pendentes",
        "em_producao",
        "peso_liquido",
        "peso_liquido_ajustado",
        "num_of_abertas",
        "qtde_of_abertas",
        "qtde_of_abertas_unica",
        "Necessidade",
        "Nec_kg",
        "Nec_kg_total_base",
        "saldo_of_x_necessidade",
        "consumo_total",
        "consumo_diario",
    ]

    for col in colunas_numericas:
        if col in df_export.columns:
            casas = 0 if col == "num_of_abertas" else 2
            df_export[col] = df_export[col].apply(lambda x: formatar_numero_br(x, casas))

    return df_export.to_csv(index=False, sep=";", encoding="utf-8-sig")


def render_card_resumo(titulo, valor, subtitulo="", cor_fundo="#f6e3e6"):
    st.markdown(
        f"""
        <div style="
            background:{cor_fundo};
            border-radius:18px;
            padding:18px 20px;
            box-shadow:0 2px 10px rgba(0,0,0,0.08);
            min-height:120px;
            margin-bottom:10px;
        ">
            <div style="
                font-size:15px;
                font-weight:700;
                color:#4b5563;
                margin-bottom:10px;
            ">
                {titulo}
            </div>
            <div style="
                font-size:22px;
                font-weight:800;
                color:#111827;
                margin-bottom:8px;
            ">
                {valor}
            </div>
            <div style="
                font-size:13px;
                color:#374151;
                line-height:1.6;
                white-space:pre-line;
            ">
                {subtitulo}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def montar_cards_por_tipo(df):
    if df.empty or "tipo_material" not in df.columns:
        return

    tipos = sorted(df["tipo_material"].dropna().astype(str).unique().tolist())

    if not tipos:
        return

    st.markdown("### Resumo por Tipo de Material")
    with st.expander("Resumo por Tipo de Material", expanded=False):
        cols = st.columns(min(len(tipos), 4))

        for i, tipo in enumerate(tipos):
            df_tipo = df[df["tipo_material"] == tipo].copy()

            total_produtos = len(df_tipo)

            total_vermelhos = 0
            if "SEMAFORO" in df_tipo.columns:
                total_vermelhos = int((df_tipo["SEMAFORO"] == "VERMELHO").sum())

            if "BASE" in df_tipo.columns and "Nec_kg_total_base" in df_tipo.columns:
                nec_total_kg = df_tipo[["BASE", "Nec_kg_total_base"]].drop_duplicates()["Nec_kg_total_base"].sum()
            else:
                nec_total_kg = 0

            if "BASE" in df_tipo.columns and "qtde_of_abertas_unica" in df_tipo.columns:
                of_total_kg = df_tipo[["BASE", "qtde_of_abertas_unica"]].drop_duplicates()["qtde_of_abertas_unica"].sum()
            else:
                of_total_kg = 0

            if "BASE" in df_tipo.columns and "SEMAFORO_TOTAL" in df_tipo.columns:
                bases_vermelhas = int(
                    (
                        df_tipo[["BASE", "SEMAFORO_TOTAL"]]
                        .drop_duplicates()["SEMAFORO_TOTAL"] == "VERMELHO"
                    ).sum()
                )
            else:
                bases_vermelhas = 0

            subtitulo = (
                f"{tipo}: {total_produtos} produtos | Vermelhos item: {total_vermelhos}\n"
                f"Nec. total: {formatar_numero_br(nec_total_kg, 2)} Kg\n"
                f"OF aberta: {formatar_numero_br(of_total_kg, 2)} Kg\n"
                f"Bases vermelhas: {bases_vermelhas}"
            )

            with cols[i % len(cols)]:
                render_card_resumo(
                    titulo=f"Tipo {tipo}",
                    valor=f"{formatar_numero_br(nec_total_kg, 2)} Kg",
                    subtitulo=subtitulo,
                    cor_fundo="#f6e3e6"
                )


def main():
    st.title("Reposição de Estoque")
    st.caption("Análise de necessidade unitária e total por BASE.")

    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2.5rem;
                padding-bottom: 2rem;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    try:
        periodo_dias = st.sidebar.selectbox(
        "Período de consumo (dias)",
        options=[30, 60, 90, 120, 180, 365],
        index=0
        )
        #df = preparar_dataframe_produtos()
        df = preparar_dataframe_produtos(dias_consumo=periodo_dias)
        if df.empty:
            st.warning("Nenhum registro encontrado.")
            return

        st.success(f"{len(df)} registros carregados com sucesso.")

        total_itens = len(df)
        total_item_vermelho = int((df["SEMAFORO"] == "VERMELHO").sum()) if "SEMAFORO" in df.columns else 0
        total_total_vermelho = int((df["SEMAFORO_TOTAL"] == "VERMELHO").sum()) if "SEMAFORO_TOTAL" in df.columns else 0
        total_ofs_abertas = int(df["num_of_abertas"].sum()) if "num_of_abertas" in df.columns else 0

        if "Nec_kg_total_base" in df.columns and "BASE" in df.columns:
            kg_necessidade_total = df[["BASE", "Nec_kg_total_base"]].drop_duplicates()["Nec_kg_total_base"].sum()
        else:
            kg_necessidade_total = 0

        if "qtde_of_abertas_unica" in df.columns and "BASE" in df.columns:
            kg_of_aberta_unica = df[["BASE", "qtde_of_abertas_unica"]].drop_duplicates()["qtde_of_abertas_unica"].sum()
        else:
            kg_of_aberta_unica = 0

        st.markdown("### Indicadores Gerais")
        with st.expander("Indicadores Gerais", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                render_card_resumo(
                    "Total de Itens",
                    formatar_numero_br(total_itens, 0),
                    f"Itens com necessidade analisada: {formatar_numero_br(total_itens, 0)}",
                    "#eef2ff"
                )

            with col2:
                render_card_resumo(
                    "Semáforo Item Vermelho",
                    formatar_numero_br(total_item_vermelho, 0),
                    "Itens com necessidade unitária negativa",
                    "#fee2e2"
                )

            with col3:
                render_card_resumo(
                    "Semáforo Total Vermelho",
                    formatar_numero_br(total_total_vermelho, 0),
                    "Bases cuja OF não cobre a necessidade total",
                    "#fef3c7"
                )

            with col4:
                render_card_resumo(
                    "OFs Abertas",
                    formatar_numero_br(total_ofs_abertas, 0),
                    f"Necessidade total: {formatar_numero_br(kg_necessidade_total, 2)} Kg\nOF aberta única: {formatar_numero_br(kg_of_aberta_unica, 2)} Kg",
                    "#dcfce7"
                )

            montar_cards_por_tipo(df)

        st.sidebar.header("Filtros")

        opcoes_tipo = sorted(df["tipo_material"].dropna().astype(str).unique().tolist()) if "tipo_material" in df.columns else []
        opcoes_semaforo = sorted(df["SEMAFORO"].dropna().astype(str).unique().tolist()) if "SEMAFORO" in df.columns else []
        opcoes_semaforo_total = sorted(df["SEMAFORO_TOTAL"].dropna().astype(str).unique().tolist()) if "SEMAFORO_TOTAL" in df.columns else []
        opcoes_unidade = sorted(df["unidade_medida"].dropna().astype(str).unique().tolist()) if "unidade_medida" in df.columns else []
        opcoes_base = sorted(df["BASE"].dropna().astype(str).unique().tolist()) if "BASE" in df.columns else []
        opcoes_codigo = sorted(df["codigo_produto_material"].dropna().astype(str).unique().tolist()) if "codigo_produto_material" in df.columns else []

        filtro_tipo = st.sidebar.multiselect(
            "Tipo de Material",
            options=opcoes_tipo,
            default=opcoes_tipo
        )

        filtro_semaforo = st.sidebar.multiselect(
            "Semáforo Item",
            options=opcoes_semaforo,
            default=opcoes_semaforo
        )

        filtro_semaforo_total = st.sidebar.multiselect(
            "Semáforo Total",
            options=opcoes_semaforo_total,
            default=opcoes_semaforo_total
        )

        filtro_unidade = st.sidebar.multiselect(
            "Unidade de Medida",
            options=opcoes_unidade,
            default=opcoes_unidade
        )

        filtro_base = st.sidebar.multiselect(
            "BASE",
            options=opcoes_base
        )

        filtro_codigo = st.sidebar.multiselect(
            "Código do Produto",
            options=opcoes_codigo
        )

        filtro_of = st.sidebar.multiselect(
            "Ordens de Fabricação",
            options=["Com OF Aberta", "Sem OF Aberta"],
            default=["Com OF Aberta", "Sem OF Aberta"]
        )

        df_filtrado = df.copy()

        if filtro_tipo and "tipo_material" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["tipo_material"].isin(filtro_tipo)]

        if filtro_semaforo and "SEMAFORO" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["SEMAFORO"].isin(filtro_semaforo)]

        if filtro_semaforo_total and "SEMAFORO_TOTAL" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["SEMAFORO_TOTAL"].isin(filtro_semaforo_total)]

        if filtro_unidade and "unidade_medida" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["unidade_medida"].isin(filtro_unidade)]

        if filtro_base and "BASE" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["BASE"].isin(filtro_base)]

        if filtro_codigo and "codigo_produto_material" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["codigo_produto_material"].isin(filtro_codigo)]

        if filtro_of and "num_of_abertas" in df_filtrado.columns:
            condicoes = []

            if "Com OF Aberta" in filtro_of:
                condicoes.append(df_filtrado["num_of_abertas"] > 0)

            if "Sem OF Aberta" in filtro_of:
                condicoes.append(df_filtrado["num_of_abertas"] <= 0)

            if condicoes:
                mascara = condicoes[0]
                for cond in condicoes[1:]:
                    mascara = mascara | cond
                df_filtrado = df_filtrado[mascara]

        st.markdown("### Resultado")

        todas_colunas = list(df_filtrado.columns)

        colunas_padrao = [
            "codigo_produto_material",
            "tipo_material",
            "unidade_medida",
            "BASE",
            "quantidade",
            "estoque_minimo",
            "em_producao",
            "num_of_abertas",
            "qtde_of_abertas_unica",
            "Necessidade",
            "Nec_kg",
            "Nec_kg_total_base",
            "consumo_total",
            "consumo_diario",
            "SEMAFORO",
            "SEMAFORO_TOTAL",
        ]

        colunas_padrao = [col for col in colunas_padrao if col in todas_colunas]

        colunas_visiveis = st.sidebar.multiselect(
            "Colunas visíveis na tabela",
            options=todas_colunas,
            default=colunas_padrao
        )

        if not colunas_visiveis:
            st.warning("Selecione ao menos uma coluna para exibir a tabela.")
            return

        df_exibicao = df_filtrado[colunas_visiveis].copy()

        colunas_formatar = [
            "quantidade",
            "estoque_minimo",
            "dias_reposicao_fornecedor",
            "pedidos_em_aberto",
            "reserva_planejamento",
            "solicit_compras",
            "compras_pendentes",
            "em_producao",
            "peso_liquido",
            "peso_liquido_ajustado",
            "qtde_of_abertas",
            "qtde_of_abertas_unica",
            "Necessidade",
            "Nec_kg",
            "Nec_kg_total_base",
            "saldo_of_x_necessidade",
            "consumo_total",
            "consumo_diario",
        ]

        for col in colunas_formatar:
            if col in df_exibicao.columns:
                df_exibicao[col] = df_exibicao[col].apply(lambda x: formatar_numero_br(x, 2))

        if "num_of_abertas" in df_exibicao.columns:
            try:
                df_exibicao["num_of_abertas"] = df_exibicao["num_of_abertas"].fillna(0).astype(int)
            except Exception:
                pass

        styled = df_exibicao.style

        if "SEMAFORO" in df_exibicao.columns:
            styled = styled.map(colorir_semaforo, subset=["SEMAFORO"])

        if "SEMAFORO_TOTAL" in df_exibicao.columns:
            styled = styled.map(colorir_semaforo, subset=["SEMAFORO_TOTAL"])

        st.dataframe(
            styled,
            use_container_width=True,
            hide_index=True
        )

        csv = preparar_csv_brasileiro(df_filtrado)

        st.download_button(
            label="Baixar CSV",
            data=csv,
            file_name="reposicao_estoque.csv",
            mime="text/csv"
        )

    except Exception as e:
        import traceback
        st.error(f"Erro ao carregar os dados: {e}")
        st.code(traceback.format_exc())
