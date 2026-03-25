import pandas as pd
from database import get_connection


def formatar_numero_br(valor, casas=2):
    try:
        return f"{float(valor):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return valor


def carregar_requisicoes() -> pd.DataFrame:
    sql = """
        SELECT
            codigo_filial,
            cod_unico_emp,
            requisicao,
            sequencia,
            seq_inf,
            data_abertura,
            status,
            desc_status,
            numero_da_of,
            grupo_prod,
            desc_grupo_prod,
            grupo_compl,
            subgrupo_prod,
            desc_subgrupo_prod,
            subgrupo_compl,
            produto_of,
            desc_produto_of,
            centro_custo,
            desc_centro_custo,
            centro_custo_compl,
            material,
            desc_material,
            unidade,
            quantidade,
            custo_unitario,
            custo_total,
            aplicacao,
            deposito,
            nro_lote,
            peso_bruto_caixa,
            maquina,
            desc_maquina,
            cod_historico,
            desc_historico,
            req_a_maior
        FROM REQUISICOES
    """

    conn = get_connection()
    try:
        df = pd.read_sql(sql, conn)
    finally:
        conn.close()

    return df

def preparar_dataframe_consumo(dias=30):
    df = carregar_requisicoes()

    if df.empty:
        return df

    df = df.copy()
    df.columns = [col.strip() for col in df.columns]

    # Conversões
    if "data_abertura" in df.columns:
        df["data_abertura"] = pd.to_datetime(df["data_abertura"], errors="coerce")

    if "status" in df.columns:
        df["status"] = df["status"].astype(str).str.strip().str.upper()

    for col in ["quantidade", "custo_unitario", "custo_total"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "material" in df.columns:
        df["material"] = df["material"].astype(str).str.strip()

    if "desc_material" in df.columns:
        df["desc_material"] = df["desc_material"].astype(str).str.strip()

    if "unidade" in df.columns:
        df["unidade"] = df["unidade"].astype(str).str.strip()

    # Somente movimentações válidas
    df = df[df["status"].isin(["R", "D"])].copy()

    # Últimos X dias com base na maior data da tabela
    if "data_abertura" in df.columns and not df["data_abertura"].isna().all():
        data_final = df["data_abertura"].max().normalize()
        data_inicial = data_final - pd.Timedelta(days=dias - 1)
        df = df[
            (df["data_abertura"] >= data_inicial) &
            (df["data_abertura"] <= data_final + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        ].copy()

    # Consumo líquido
    # R = consumo positivo
    # D = devolução negativa
    df["quantidade_mov"] = df["quantidade"]

    df.loc[df["status"] == "D", "quantidade_mov"] = df.loc[df["status"] == "D", "quantidade_mov"] * -1
    df.loc[df["status"] == "D", "custo_total"] = df.loc[df["status"] == "D", "custo_total"] * -1

    df["data"] = df["data_abertura"].dt.date

    return df


def resumo_consumo_material(df):
    if df.empty:
        return pd.DataFrame()

    agrupado = (
        df.groupby(["material", "desc_material", "unidade"], dropna=False, as_index=False)
        .agg(
            consumo_total=("quantidade_mov", "sum"),
            custo_total_consumo=("custo_total", "sum"),
            total_movimentos=("requisicao", "count"),
            dias_com_movimento=("data", "nunique"),
        )
    )

    dias_periodo = df["data"].nunique() if "data" in df.columns and not df.empty else 0
    dias_periodo = max(dias_periodo, 1)

    agrupado["consumo_diario"] = agrupado["consumo_total"] / dias_periodo

    agrupado = agrupado.sort_values(by="consumo_total", ascending=False).reset_index(drop=True)
    return agrupado


def consumo_diario_material(df):
    if df.empty:
        return pd.DataFrame()

    diario = (
        df.groupby(["data", "material", "desc_material", "unidade"], dropna=False, as_index=False)
        .agg(
            consumo_dia=("quantidade_mov", "sum"),
            custo_dia=("custo_total", "sum"),
        )
    )

    diario = diario.sort_values(by=["material", "data"]).reset_index(drop=True)
    return diario


def preparar_csv_brasileiro(df):
    df_export = df.copy()

    colunas_numericas = [
        "consumo_total",
        "consumo_diario",
        "custo_total_consumo",
        "consumo_dia",
        "custo_dia",
        "quantidade",
        "quantidade_mov",
        "custo_unitario",
        "custo_total",
    ]

    for col in colunas_numericas:
        if col in df_export.columns:
            df_export[col] = df_export[col].apply(lambda x: formatar_numero_br(x, 2))

    return df_export.to_csv(index=False, sep=";", encoding="utf-8-sig")