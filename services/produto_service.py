import pandas as pd
from database import get_connection


COLUNAS_FINAIS = [
    "codigo_produto_material",
    "descricao_produto",
    "unidade_medida",
    "tipo_material",
    "quantidade",
    "estoque_minimo",
    "dias_reposicao_fornecedor",
    "pedidos_em_aberto",
    "reserva_planejamento",
    "solicit_compras",
    "compras_pendentes",
    "em_producao",
    "deposito_indisp",
    "peso_liquido",
    "peso_liquido_ajustado",
    "data_planejamento",
    "BASE",
    "num_of_abertas",
    "qtde_of_abertas",
    "qtde_of_abertas_unica",
    "Necessidade",
    "Nec_kg",
    "Nec_kg_total_base",
    "saldo_of_x_necessidade",
    "consumo_total",
    "consumo_diario",
    "SEMAFORO",
    "SEMAFORO_TOTAL",
]


def carregar_produtos() -> pd.DataFrame:
    query = """
        SELECT
            codigo_produto_material,
            descricao_produto,
            tipo_material,
            unidade_medida,
            estoque_minimo,
            dias_reposicao_fornecedor,
            pedidos_em_aberto,
            reserva_planejamento,
            solicit_compras,
            compras_pendentes,
            deposito_indisp,
            em_producao,
            peso_liquido,
            data_planejamento
        FROM PRODUTO
        WHERE tipo_material IN ('FO', 'PI', 'MP', 'PA')
    """

    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    return df


def carregar_estoque_consolidado() -> pd.DataFrame:
    query = """
        SELECT
            produto,
            SUM(quantidade) AS quantidade
        FROM POSICAO_ESTOQUE_ATUAL
        WHERE deposito NOT IN ('AVARIA', 'N CONF', 'VENC', 'LAB')
        GROUP BY produto
    """

    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    return df


def carregar_ordens_fabric_abertas() -> pd.DataFrame:
    query = """
        SELECT
            produto,
            COUNT(numero_da_of) AS num_of_abertas,
            SUM(qtde) AS qtde_of_abertas
        FROM ORDEM_FABRIC
        WHERE status_of = 'A'
        GROUP BY produto
    """

    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    return df


def carregar_consumo_por_material(dias=30) -> pd.DataFrame:
    query = f"""
        SELECT
            material,
            data_abertura,
            status,
            quantidade
        FROM REQUISICOES
        WHERE status IN ('R', 'D')
          AND data_abertura >= DATE_SUB(CURDATE(), INTERVAL {int(dias)} DAY)
    """

    conn = get_connection()
    try:
        df = pd.read_sql(query, conn)
    finally:
        conn.close()

    if df.empty:
        return pd.DataFrame(columns=["material", "consumo_total", "consumo_diario"])

    df["material"] = df["material"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.upper()
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)

    df["quantidade_mov"] = df["quantidade"]
    df.loc[df["status"] == "D", "quantidade_mov"] = df.loc[df["status"] == "D", "quantidade_mov"] * -1

    consumo = (
        df.groupby("material", as_index=False)
        .agg(consumo_total=("quantidade_mov", "sum"))
    )

    dias = max(int(dias), 1)
    consumo["consumo_diario"] = consumo["consumo_total"] / dias

    return consumo


def extrair_base(codigo_produto_material: str, tipo_material: str) -> str:
    if pd.isna(codigo_produto_material):
        return ""

    codigo = str(codigo_produto_material).strip()
    tipo = str(tipo_material).strip().upper() if pd.notna(tipo_material) else ""

    if tipo == "PA":
        return codigo.split(".")[0]

    return codigo


def tratar_colunas_numericas(df: pd.DataFrame) -> pd.DataFrame:
    colunas_numericas = [
        "quantidade",
        "estoque_minimo",
        "dias_reposicao_fornecedor",
        "pedidos_em_aberto",
        "reserva_planejamento",
        "solicit_compras",
        "compras_pendentes",
        "em_producao",
        "deposito_indisp",
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
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def calcular_necessidade(df: pd.DataFrame) -> pd.DataFrame:
    df["Necessidade"] = (
        (
            df["quantidade"]
            + df["em_producao"]
            + df["compras_pendentes"]
            - df["deposito_indisp"]   #  NOVO
        )
        - (
            df["pedidos_em_aberto"]
            + df["reserva_planejamento"]
            + df["estoque_minimo"]
        )
    )
    return df


def ajustar_peso_liquido(df: pd.DataFrame) -> pd.DataFrame:
    def definir_peso(row):
        tipo = str(row["tipo_material"]).strip().upper()

        if tipo == "PA":
            return row["peso_liquido"] if pd.notna(row["peso_liquido"]) else 0

        return 1

    df["peso_liquido_ajustado"] = df.apply(definir_peso, axis=1)
    return df


def calcular_necessidade_kg(df: pd.DataFrame) -> pd.DataFrame:
    df["Nec_kg"] = df["Necessidade"] * df["peso_liquido_ajustado"]
    return df


def aplicar_semaforo(df: pd.DataFrame) -> pd.DataFrame:
    def definir_semaforo(valor):
        if valor < 0:
            return "VERMELHO"
        elif valor == 0:
            return "AMARELO"
        return "VERDE"

    df["SEMAFORO"] = df["Necessidade"].apply(definir_semaforo)
    return df


def consolidar_por_base(df: pd.DataFrame) -> pd.DataFrame:
    df["Nec_kg_total_base"] = df.groupby("BASE")["Nec_kg"].transform("sum")
    df["qtde_of_abertas_unica"] = df.groupby("BASE")["qtde_of_abertas"].transform("max")

    def calcular_saldo(row):
        nec_total = row["Nec_kg_total_base"]
        of_unica = row["qtde_of_abertas_unica"]

        if nec_total < 0:
            return of_unica - abs(nec_total)
        return of_unica

    df["saldo_of_x_necessidade"] = df.apply(calcular_saldo, axis=1)

    return df


def aplicar_semaforo_total(df: pd.DataFrame) -> pd.DataFrame:
    def definir_semaforo_total(row):
        nec_total = row["Nec_kg_total_base"]
        of_unica = row["qtde_of_abertas_unica"]

        if nec_total >= 0:
            return "VERDE"

        necessidade_total_abs = abs(nec_total)

        if of_unica == 0:
            return "VERMELHO"
        elif of_unica < necessidade_total_abs:
            return "VERMELHO"
        elif of_unica == necessidade_total_abs:
            return "AMARELO"
        else:
            return "VERDE"

    df["SEMAFORO_TOTAL"] = df.apply(definir_semaforo_total, axis=1)
    return df


def formatar_data(df: pd.DataFrame) -> pd.DataFrame:
    if "data_planejamento" in df.columns:
        df["data_planejamento"] = pd.to_datetime(
            df["data_planejamento"], errors="coerce"
        ).dt.strftime("%d/%m/%Y")
        df["data_planejamento"] = df["data_planejamento"].fillna("")
    return df


def preparar_dataframe_produtos(dias_consumo=30) -> pd.DataFrame:
    df_produto = carregar_produtos()
    df_estoque = carregar_estoque_consolidado()
    df_of = carregar_ordens_fabric_abertas()
    df_consumo = carregar_consumo_por_material(dias=dias_consumo)

    df = df_produto.merge(
        df_estoque,
        how="left",
        left_on="codigo_produto_material",
        right_on="produto"
    )

    df["quantidade"] = df["quantidade"].fillna(0)
    df = df.drop(columns=["produto"], errors="ignore")

    df = tratar_colunas_numericas(df)

    df = df[df["estoque_minimo"] != 0].copy()

    df["BASE"] = df.apply(
        lambda row: extrair_base(row["codigo_produto_material"], row["tipo_material"]),
        axis=1
    )

    df = df.merge(
        df_of,
        how="left",
        left_on="BASE",
        right_on="produto"
    )

    df = df.drop(columns=["produto"], errors="ignore")

    df = df.merge(
        df_consumo,
        how="left",
        left_on="BASE",
        right_on="material"
    )

    df = df.drop(columns=["material"], errors="ignore")

    df = tratar_colunas_numericas(df)

    df = calcular_necessidade(df)
    df = ajustar_peso_liquido(df)
    df = calcular_necessidade_kg(df)
    df = aplicar_semaforo(df)
    df = consolidar_por_base(df)
    df = aplicar_semaforo_total(df)
    df = formatar_data(df)
    df = tratar_colunas_numericas(df)

    for col in COLUNAS_FINAIS:
        if col not in df.columns:
            df[col] = ""

    df = df[COLUNAS_FINAIS].copy()

    return df
